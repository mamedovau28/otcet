import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

#COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"],
    "охват": ["охват", "reach"]
}

PLATFORM_MAPPING = {
    "площадка": ["площадка", "название сайта", "ресурс"]
}


def standardize_columns(df, mapping):
    df.columns = df.columns.astype(str).str.lower().str.strip()
    df = df.loc[:, df.columns != 'nan']
    
    column_map = {}
    for standard_col, possible_names in mapping.items():
        for col in df.columns:
            if any(word in col for word in possible_names):
                column_map[standard_col] = col
                break
                
    return df.rename(columns=column_map), column_map
def filter_columns(df, is_mp=False):
    if is_mp:
        required_columns = []

        df.replace({"-": 0}, inplace=True)
        df.fillna(0, inplace=True)

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
                
        return df[required_columns] if required_columns else df
    return df
def process_data(df):
    df, col_map = standardize_columns(df, COLUMN_MAPPING)
    df.fillna(0, inplace=True)

    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    for key in ["показы", "клики", "охват", "расход"]:
        if key in col_map and not pd.api.types.is_numeric_dtype(df[col_map[key]]):
            df[col_map[key]] = df[col_map[key]].astype(str).str.replace(r"[^\d]", "", regex=True)
            df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)

    if "расход" in col_map:
        df[col_map["расход"]] = df[col_map["расход"]] / 100

    if "охват" in col_map and "показы" in col_map:
        def adjust_coverage(row):
            coverage = row[col_map["охват"]]
            impressions = row[col_map["показы"]]
            if coverage > 0 and impressions > 0 and impressions / coverage > 10:
                return impressions * coverage / 100
            return round(coverage)
        df["охват"] = df.apply(adjust_coverage, axis=1)

    if "расход" in col_map:
        df["расход с ндс"] = df[col_map["расход"]] * 1.2
    if "клики" in col_map and "показы" in col_map:
        df["ctr"] = df.apply(lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] > 0 else 0, axis=1)

    df = filter_columns(df)

    return df, col_map

def clean_mp(mp_df):
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

def find_column(df, keywords):
    """
    Функция для поиска столбцов, содержащих ключевые слова.
    """
    found_columns = {}
    for keyword in keywords:
        column_matches = [col for col in df.columns if re.search(keyword, col, re.IGNORECASE)]
        if column_matches:
            found_columns[keyword] = column_matches[0]  # Сохраняем первый найденный столбец
    return found_columns

def calculate_campaign_period(df, col_map):
    """
    Определяем дату начала и конца рекламной кампании.
    """
    # Находим первую дату с показами больше 10
    df_filtered = df[df[col_map["показы"]] > 10]
    if not df_filtered.empty:
        start_date = df_filtered[col_map["дата"]].min().date()
    else:
        st.error("Нет данных о показах больше 10.")
        return None, None
    
    # Конец кампании по умолчанию - последний день месяца
    end_date = datetime(start_date.year, start_date.month, 1) + timedelta(days=32)
    end_date = end_date.replace(day=1) - timedelta(days=1)

    return start_date, end_date

def distribute_mp_data(mp_df, start_date, end_date, col_map):
    """
    Равномерно распределяем данные по дням и возвращаем средние значения.
    """
    # Вычисляем количество дней в рекламном периоде
    num_days = (end_date - start_date).days + 1
    
    # Получаем сумму показов, кликов, охвата, расхода из медиаплана
    total_impressions = mp_df[col_map["показы"]].sum()
    total_clicks = mp_df[col_map["клики"]].sum()
    total_reach = mp_df[col_map["охват"]].sum()
    total_spend_nds = mp_df[col_map["бюджет с ндс"]].sum()
    
    # Равномерно распределяем данные по дням
    daily_impressions = total_impressions / num_days
    daily_clicks = total_clicks / num_days
    daily_reach = total_reach / num_days
    daily_spend = total_spend_nds / num_days

    return daily_impressions, daily_clicks, daily_reach, daily_spend

def analyze_campaign(mp_df, df, col_map):
    if mp_df is None or df is None:
        st.error("Ошибка: не загружен один из файлов (МП или отчет).")
        return

    matched_platform = False
    mp_platform_column = find_column(mp_df, ["площадка", "название сайта", "ресурс"])
    report_platform_column = find_column(df, ["площадка", "название сайта", "ресурс"])

    if mp_platform_column and report_platform_column:
        for mp_platform in mp_df[mp_platform_column[0]]:
            for report_platform in df[report_platform_column[0]]:
                if mp_platform.lower() == report_platform.lower():
                    matched_platform = True
                    st.write(f"Найдено совпадение по площадке: {mp_platform}")
                    break
            if matched_platform:
                break

    if not matched_platform:
        st.write("Не найдено совпадений по площадке.")
        return
    
    found_columns = find_column(mp_df, ["показы", "клики", "охват", "ндс"])

    if "показы" not in found_columns or "клики" not in found_columns or "охват" not in found_columns:
        st.error("Не все необходимые столбцы (показы, клики, охват) найдены.")
        return
    
    if "ндс" not in found_columns:
        st.error("Не найден столбец с бюджетом с НДС.")
        return

    start_date, end_date = calculate_campaign_period(df, col_map)
    if start_date is None or end_date is None:
        return

    st.write(f"Дата начала рекламной кампании: {start_date}")
    st.write(f"Дата окончания рекламной кампании: {end_date}")

    daily_impressions, daily_clicks, daily_reach, daily_spend = distribute_mp_data(mp_df, start_date, end_date, found_columns)

    st.write(f"Среднее количество показов в день: {daily_impressions:.0f}")
    st.write(f"Среднее количество кликов в день: {daily_clicks:.0f}")
    st.write(f"Среднее количество охвата в день: {daily_reach:.0f}")
    st.write(f"Средний расход с НДС в день: {daily_spend:.2f} руб.")

    total_impressions_report = df[col_map["показы"]].sum()
    total_clicks_report = df[col_map["клики"]].sum()
    total_reach_report = df[col_map["охват"]].sum()
    total_spend_report = df[col_map["расход с ндс"]].sum()

    st.write("Итоговые данные по отчету:")
    st.write(f"Показы: {total_impressions_report:.0f}")
    st.write(f"Клики: {total_clicks_report:.0f}")
    st.write(f"Охват: {total_reach_report:.0f}")
    st.write(f"Расход с НДС: {total_spend_report:.2f} руб.")

    st.write("Сравнение данных медиаплана и отчета:")

    st.write(f"Разница в показах: {total_impressions_report - daily_impressions * (end_date - start_date).days:.0f}")
    st.write(f"Разница в кликах: {total_clicks_report - daily_clicks * (end_date - start_date).days:.0f}")
    st.write(f"Разница в охвате: {total_reach_report - daily_reach * (end_date - start_date).days:.0f}")
    st.write(f"Разница в расходе: {total_spend_report - daily_spend * (end_date - start_date).days:.2f} руб.")

        
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

        if mp_df is not None:  # Если медиаплан был загружен
            match_message = check_matching_campaign(mp_df, custom_campaign_name)
            st.write(match_message)

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
            
            # Новый график: столбчатая диаграмма для кликов
            plt.figure(figsize=(10, 3))

            # Столбцы для кликов
            plt.bar(df_filtered[col_map["дата"]], df_filtered["клики"], color='r', alpha=0.7, label="Клики")

            plt.title(f"Клики по дням для {custom_campaign_name}")
            plt.xticks(rotation=45)
            plt.grid(True, axis='y')
            plt.legend()
            st.pyplot(plt)  # Отображаем график с кликами в Streamlit
    
    st.dataframe(df)
