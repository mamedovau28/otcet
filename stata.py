import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Словарь для сопоставления названий колонок в отчетах
COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"],
    "охват": ["охват", "reach"]
}

# Словарь для сопоставления названий колонок в МП (рекламные площадки)
PLATFORM_MAPPING = {
    "площадка": ["площадка", "название сайта", "ресурс"]
}

def standardize_columns(df, mapping):
    """
    Приводит названия колонок к стандартному виду по переданному mapping.
    Все имена столбцов приводятся к нижнему регистру и обрезаются пробелы.
    Столбцы с заголовком 'nan' удаляются.
    """
    df.columns = df.columns.astype(str).str.lower().str.strip()
    # Удаляем столбцы с заголовком 'nan'
    df = df.loc[:, df.columns != 'nan']
    
    column_map = {}
    for standard_col, possible_names in mapping.items():
        for col in df.columns:
            if any(word in col for word in possible_names):
                column_map[standard_col] = col
                break
                
    return df.rename(columns=column_map), column_map

def filter_columns(df, is_mp=False):
    """
    Оставляет только нужные столбцы в определенном порядке.
    Фильтрация применяется только к файлам медиаплана (если is_mp=True).
    - дата (если есть)
    - площадка (если есть)
    - показы (если есть)
    - клики (если есть)
    - охват (если есть)
    - расход (если есть)
    - столбец, содержащий "с учетом НДС и АК" (если есть)
    """
    # Если это медиаплан, применяем фильтрацию
    if is_mp:
        required_columns = []

        # Заменяем все символы "-" и значения NaN и None на 0
        df.replace({"-": 0}, inplace=True)  # Заменяем "-" на 0
        df.fillna(0, inplace=True)  # Заменяем NaN и None на 0

        for col in df.columns:
            col_lower = col.lower().strip()

            if "дата" in col_lower:
                required_columns.append(col)
            elif any(keyword in col_lower for keyword in ["площадка", "название сайта", "ресурс"]):
                required_columns.append(col)
            elif "показ" in col_lower:
                required_columns.append(col)
            elif "клик" in col_lower:
                required_columns.append(col)
            elif "охват" in col_lower:
                required_columns.append(col)
            elif "расход" in col_lower:
                required_columns.append(col)
            elif re.search(r".* ндс и .*", col_lower):
                required_columns.append(col)
                
        # Возвращаем DataFrame с колонками в нужном порядке
        return df[required_columns] if required_columns else df
        
        # Удаляем строки, где значение в столбце "показы" равно 0
        if "показы" in df.columns:
            df = df[df["показы"] != 0]

        return df

    # Если это не медиаплан (например, отчет), возвращаем df без изменений
    return df
    
# Встраиваем в процесс обработки данных
def process_data(df):
    """
    Обрабатывает загруженные данные (Excel или Google-таблицы):
      - Стандартизирует имена колонок
      - Преобразует дату, приводит числовые значения к нужному типу
      - Рассчитывает расход с НДС и CTR
      - Очищает ненужные столбцы
    """
    df, col_map = standardize_columns(df, COLUMN_MAPPING)
    df.fillna(0, inplace=True)

    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    # Приведение к числовому типу
    for key in ["показы", "клики", "охват", "расход"]:
        if key in col_map and not pd.api.types.is_numeric_dtype(df[col_map[key]]):
            df[col_map[key]] = df[col_map[key]].astype(str).str.replace(r"[^\d]", "", regex=True)
            df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)

    if "расход" in col_map:
        df[col_map["расход"]] = df[col_map["расход"]] / 100

    # Корректировка охвата
    if "охват" in col_map and "показы" in col_map:
        def adjust_coverage(row):
            coverage = row[col_map["охват"]]
            impressions = row[col_map["показы"]]
            if coverage > 0 and impressions > 0 and impressions / coverage > 10:
                return impressions * coverage / 100
            return round(coverage)
        df["охват"] = df.apply(adjust_coverage, axis=1)

    # Расчет расхода с НДС и CTR
    if "расход" in col_map:
        df["расход с ндс"] = df[col_map["расход"]] * 1.2
    if "клики" in col_map and "показы" in col_map:
        df["ctr"] = df.apply(lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] > 0 else 0, axis=1)

    # Фильтрация нужных столбцов
    df = filter_columns(df)

    return df, col_map
    
def clean_mp(mp_df):
    """
    Ищет первую строку, содержащую слово "площадка", "название сайта" или "ресурс" (без учета регистра).
    Считает эту строку заголовочной и возвращает таблицу, начиная с этой строки.
    """
    for i, row in mp_df.iterrows():
        if row.astype(str).str.contains("площадка", case=False, na=False).any() or \
           row.astype(str).str.contains("название сайта", case=False, na=False).any() or \
           row.astype(str).str.contains("ресурс", case=False, na=False).any():
            mp_df = mp_df.iloc[i:].reset_index(drop=True)
            mp_df.columns = mp_df.iloc[0]
            mp_df = mp_df[1:].reset_index(drop=True)
            return mp_df
    return None

def process_mp(mp_df):
    """
    Обрабатывает медиаплан (МП):
      - Вызывает clean_mp, чтобы найти строку с заголовками (начало таблицы).
      - Стандартизирует имена колонок по PLATFORM_MAPPING.
      - Возвращает очищенную таблицу и mapping найденных столбцов.
    """
    mp_df = clean_mp(mp_df)
    if mp_df is None:
        st.error("Ошибка: не удалось найти строку с заголовками, содержащую 'площадка', 'название сайта' или 'ресурс'.")
        return None, {}

    mp_df, col_map = standardize_columns(mp_df, PLATFORM_MAPPING)

    # Применяем фильтрацию столбцов сразу после стандартизации
    mp_df = filter_columns(mp_df, is_mp=True)

    return mp_df, col_map
    
st.title("Анализ рекламных кампаний")

st.header("Загрузите медиаплан (МП) (только Excel)")
mp_file = st.file_uploader("Выберите файл с медиапланом", type=["xlsx"], key="mp_uploader")

mp_df = None
if mp_file:
    # Чтение Excel файла
    xls = pd.ExcelFile(mp_file)
    sheet_names = xls.sheet_names
    if len(sheet_names) > 1:
        sheet_name = st.selectbox("Выберите лист с медиапланом", sheet_names, key="mp_sheet_select")
    else:
        sheet_name = sheet_names[0]
    
    # Загрузка данных с выбранного листа
    mp_df = pd.read_excel(mp_file, sheet_name=sheet_name)
    st.write("Медиаплан загружен:", sheet_name)

    # Обработка медиаплана, включая фильтрацию столбцов
    mp_df, mp_col_map = process_mp(mp_df)  # Фильтрация теперь будет применяться здесь

    if mp_df is not None:
        st.subheader("Обработанный медиаплан")

        # Убираем дубликаты столбцов
        mp_df = mp_df.loc[:, ~mp_df.columns.duplicated()].copy()

        # Фильтрация столбцов с нужным порядком и удаление строк с нулевыми показами
        mp_df = filter_columns(mp_df, is_mp=True)  # Применяем фильтрацию для медиаплана

        # Находим столбец, который содержит "показы" в своем названии
        show_column = [col for col in mp_df.columns if "показы" in col.lower()]

        if show_column:
            # Преобразуем столбец в числовой тип
            mp_df[show_column[0]] = pd.to_numeric(mp_df[show_column[0]], errors="coerce")  # Преобразуем в числовой тип, NaN для ошибок

            # Удаляем строки, где показы = 0 или NaN
            mp_df = mp_df[mp_df[show_column[0]] > 0]  # Оставляем только строки с показами больше 0

        # Ищем столбец, который содержит "НДС"
        ndc_column = [col for col in mp_df.columns if "ндс" in col.lower()]

        # Если такой столбец найден, приводим его к числовому типу и удаляем строки с нулями
        if ndc_column:
            ndc_column_name = ndc_column[0]  # Получаем имя столбца
            mp_df[ndc_column_name] = pd.to_numeric(mp_df[ndc_column_name], errors="coerce")  # Преобразуем в числовой тип, NaN для ошибок
            # Удаляем строки, где значение в столбце НДС = 0 или NaN
            mp_df = mp_df[mp_df[ndc_column_name] > 0]  # Оставляем только строки с показателями больше 0

        # Оставляем только те столбцы, где количество ненулевых значений больше 1
        mp_df = mp_df.loc[:, (mp_df != 0).sum(axis=0) > 1]

        # Отображаем обработанный медиаплан
        st.dataframe(mp_df)

# === Загрузка отчетов ===
st.header("Загрузите данные (Excel или Google-таблицы)")

for i in range(1, 11):
    upload_option = st.selectbox(f"Способ загрузки файла {i}", ["Не выбрано", "Загрузить Excel-файл", "Ссылка на Google-таблицу"], key=f"upload_option_{i}")

    df = None
    campaign_name = None

    if upload_option == "Загрузить Excel-файл":
        uploaded_file = st.file_uploader(f"Загрузите Excel-файл {i}", type=["xlsx"], key=f"file_uploader_{i}")
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            campaign_name = uploaded_file.name.split(".")[0]

    elif upload_option == "Ссылка на Google-таблицу":
        google_sheet_url = st.text_input(f"Ссылка на Google-таблицу {i}", key=f"google_sheet_url_{i}")
        if google_sheet_url:
            try:
                sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
                gid = google_sheet_url.split("gid=")[1].split("&")[0] if "gid=" in google_sheet_url else "0"
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
                df = pd.read_csv(csv_url)
                campaign_name = f"Загрузка {i}"
            except Exception as e:
                st.error(f"Ошибка при загрузке CSV: {e}")

    if df is not None:
        df, col_map = process_data(df)
        custom_campaign_name = st.text_input(f"Введите название РК {i} (или оставьте по умолчанию)", value=campaign_name, key=f"campaign_name_{i}")
        st.write(f"Название РК: {custom_campaign_name}")

        if "дата" in col_map:
            min_date = df[col_map["дата"]].min().date()
            max_date = df[col_map["дата"]].max().date()
            start_date, end_date = st.date_input("Выберите период", [min_date, max_date], key=f"date_input_{i}")

            df_filtered = df[
                (df[col_map["дата"]].dt.date >= start_date) & 
                (df[col_map["дата"]].dt.date <= end_date)
            ]

            # Результаты по выбранному периоду
            needed_cols = ["показы", "клики", "охват", "расход с ндс"]
            existing_cols = [col for col in needed_cols if col in df_filtered.columns]
            summary = df_filtered[existing_cols].sum()

            total_impressions = summary.get("показы", 0)
            total_clicks = summary.get("клики", 0)
            ctr_value = total_clicks / total_impressions if total_impressions > 0 else 0
            total_reach = summary.get("охват", 0)
            total_spend_nds = summary.get("расход с ндс", 0)

            # Форматируем даты в нужный формат
            start_date_str = start_date.strftime("%d.%m.%Y")
            end_date_str = end_date.strftime("%d.%m.%Y")

            report_text = f"""
    {custom_campaign_name}
    Период: {start_date_str}-{end_date_str}
    Показы: {total_impressions:.0f}
    Клики: {total_clicks:.0f}
    CTR: {ctr_value:.2%}
    Охват: {total_reach:.0f}
    Расход с НДС: {format(total_spend_nds, ",.2f").replace(",", " ")} руб.
            """
            st.subheader(f"Итоговый отчёт {custom_campaign_name}")
            st.text_area(report_text, report_text, height=100)

            # Используем st.empty() для пустого контейнера
            container = st.empty()

            # Построение графиков
            container.pyplot(plt)
           
            # Построим график по дням
            plt.figure(figsize=(10, 6))

            # Линия для показов
            plt.plot(df_filtered[col_map["дата"]], df_filtered["показы"], marker='o', label="Показы", color='b')

            # Линия для охвата
            plt.plot(df_filtered[col_map["дата"]], df_filtered["охват"], marker='o', label="Охват", color='g')

            # Заливка фона под линией охвата
            plt.fill_between(df_filtered[col_map["дата"]], 0, df_filtered["охват"], color='g', alpha=0.2)

            plt.title(f"Показы и Охват по дням для {custom_campaign_name}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.legend()
            st.pyplot(plt)  # Отображаем график в Streamlit

            # Закрываем текущую фигуру, чтобы избежать лишних окон
            plt.close()

            # Новый график: столбчатая диаграмма для кликов
            plt.figure(figsize=(10, 3))

            # Столбцы для кликов
            plt.bar(df_filtered[col_map["дата"]], df_filtered["клики"], color='r', alpha=0.7, label="Клики")

            plt.title(f"Клики по дням для {custom_campaign_name}")
            plt.xticks(rotation=45)
            plt.grid(True, axis='y')
            plt.legend()
            st.pyplot(plt)  # Отображаем график с кликами в Streamlit

            # Закрываем текущую фигуру после отображения
            plt.close()
    st.dataframe(df)
