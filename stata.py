import streamlit as st
import pandas as pd
import re

# Словари для сопоставления названий колонок
COLUMN_MAPPING = {
    "площадка": ["площадка", "сайт", "ресурс"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "охват": ["охват", "reach"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"]
}

#def standardize_columns(df):
   # """Приводит названия колонок к стандартному виду"""
   # df.columns = df.columns.str.lower().str.strip()
   # column_map = {}
   # for standard_col, possible_names in COLUMN_MAPPING.items():
     #   for col in df.columns:
        #    if any(word in col for word in possible_names):
        #        column_map[standard_col] = col
        #        break
   # return df.rename(columns=column_map), column_map

def standardize_columns(df):
    """Функция для стандартизации названий колонок"""
    df.columns = df.columns.str.lower().str.strip()  # Приводим имена столбцов к нижнему регистру и убираем пробелы
    column_map = {}
    
    for standard_col, possible_names in COLUMN_MAPPING.items():
        for col in df.columns:
            # Убедимся, что столбец - строка, прежде чем выполнять поиск подстроки
            if isinstance(col, str) and any(word in col for word in possible_names):
                column_map[standard_col] = col
                break
    
    return df.rename(columns=column_map), column_map


def clean_mp(mp_df):
    """Ищем первую строку с названием колонок и очищаем медиаплан, начиная с проекта"""
    # Поиск строки, в которой встречается "проект" (или его вариации) в одном из столбцов
    for i, row in mp_df.iterrows():
        if row.str.contains(r'проект', case=False, na=False).any():  # Ищем слово "проект" (нечувствительно к регистру)
            mp_df = mp_df.iloc[i:].reset_index(drop=True)  # Начинаем с найденной строки
            mp_df.columns = mp_df.iloc[0]  # Первая строка становится заголовками
            mp_df = mp_df[1:].reset_index(drop=True)  # Удаляем дублирующуюся строку заголовков
            return mp_df
    return None  # Если не нашли, возвращаем None

def process_mp(mp_df):
    """Обрабатывает медиаплан: находит нужные столбцы и удаляет пустые строки"""
    mp_df = clean_mp(mp_df)  # Очищаем таблицу, начиная с проекта
    if mp_df is None:
        st.error("Ошибка: Не удалось найти таблицу в медиаплане.")
        return None

    mp_df, col_map = standardize_columns(mp_df)

    required_cols = {"площадка", "показы", "клики"}
    if not required_cols.issubset(col_map):
        st.error("Ошибка: В медиаплане нет всех обязательных столбцов ('Площадка', 'Показы', 'Клики').")
        return None

    selected_columns = [col_map[col] for col in required_cols]
    if "охват" in col_map:
        selected_columns.append(col_map["охват"])

    mp_df = mp_df[selected_columns]
    mp_df.dropna(subset=[col_map["площадка"], col_map["показы"], col_map["клики"]], inplace=True)

    return mp_df

def process_data(df):
    df, col_map = standardize_columns(df)
    df.fillna(0, inplace=True)

    # Преобразование даты
    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    # Преобразование показов, кликов, охвата и расхода
    if {"клики", "показы", "охват", "расход"}.issubset(col_map):
        for key in ["показы", "клики", "охват", "расход"]:
            if not pd.api.types.is_numeric_dtype(df[col_map[key]]):
                df[col_map[key]] = (
                    df[col_map[key]]
                    .astype(str)
                    .str.replace(r"[^\d]", "", regex=True)  # Оставляем только цифры
                )
                df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)  # Преобразуем в числа

    df[col_map["расход"]] = df[col_map["расход"]] / 100

    # Охват
    if "охват" in col_map and "показы" in col_map:
        def adjust_coverage(row):
            coverage = row[col_map["охват"]]
            impressions = row[col_map["показы"]]

            if coverage > 0 and impressions > 0:
                if impressions / coverage > 10:  # Если показы в 10 раз больше охвата
                    return impressions * coverage / 100  # Пересчитываем охват
            return round(coverage)  # Оставляем как есть

        df["охват"] = df.apply(adjust_coverage, axis=1)

    # Расчет расхода с НДС
    df["расход с ндс"] = df[col_map["расход"]] * 1.2

    # Рассчитываем CTR
    df["ctr"] = df.apply(
        lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] > 0 else 0,
        axis=1
    )
            
    return df, col_map

# Интерфейс Streamlit
st.title("Анализ качества рекламных кампаний")

# === Загрузка МП ===
st.header("Загрузите медиаплан (только Excel)")

mp_file = st.file_uploader("Выберите файл с медиапланом", type=["xlsx"], key="mp_uploader")
mp_data = None

if mp_file:
    xls = pd.ExcelFile(mp_file)
    sheet_name = st.selectbox("Выберите лист", xls.sheet_names) if len(xls.sheet_names) > 1 else xls.sheet_names[0]
    
    mp_data = pd.read_excel(mp_file, sheet_name=sheet_name)
    mp_data = process_mp(mp_data)

    if mp_data is not None:
        st.subheader("Обработанный медиаплан")
        st.dataframe(mp_data)

# Загрузка и обработка данных (Excel или Google-таблицы)
st.header("Загрузка отчетов")

for i in range(1, 11):
    upload_option = st.selectbox(f"Способ загрузки файла {i}", ["Не выбрано", "Загрузить Excel-файл", "Ссылка на Google-таблицу"], key=f"upload_option_{i}")

    df = None
    campaign_name = None

    if upload_option == "Загрузить Excel-файл":
        uploaded_file = st.file_uploader(f"Загрузите Excel-файл {i}", type=["xlsx"], key=f"file_uploader_{i}")
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            campaign_name = uploaded_file.name.split(".")[0]  # Имя файла как название РК

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

        # Выбор периода
        if "дата" in col_map:
            min_date = df[col_map["дата"]].min().date()
            max_date = df[col_map["дата"]].max().date()
            start_date, end_date = st.date_input("Выберите период", [min_date, max_date], key=f"date_input_{i}")

            df_filtered = df[
                (df[col_map["дата"]].dt.date >= start_date) & 
                (df[col_map["дата"]].dt.date <= end_date)
            ]

            needed_cols = ["показы", "клики", "охват", "расход с ндс"]
            existing_cols = [col for col in needed_cols if col in df_filtered.columns]
            summary = df_filtered[existing_cols].sum()

            total_impressions = summary.get("показы", 0)
            total_clicks = summary.get("клики", 0)
            ctr_value = total_clicks / total_impressions if total_impressions > 0 else 0
            total_reach = summary.get("охват", 0)
            total_spend_nds = summary.get("расход с ндс", 0)

            # Генерация отчёта
            report_text = f"""
            {custom_campaign_name}
        Показы: {format(total_impressions, ",.0f").replace(",", " ")}
        Клики: {format(total_clicks, ",.0f").replace(",", " ")}
        CTR: {ctr_value:.2%}
        Охват: {format(total_reach, ",.0f").replace(",", " ")}
        Расход с НДС: {format(total_spend_nds, ",.2f").replace(",", " ")} руб.
            """

            # Вывод отчёта
            st.subheader("Итоговый отчёт")
            st.text_area(report_text, report_text, height=100)

        # Вывод таблицы
        st.dataframe(df)
