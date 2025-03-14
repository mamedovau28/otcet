import streamlit as st
import pandas as pd
import re

# Словарь для сопоставления названий колонок
COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"],
    "охват": ["охват", "reach"]
}

def standardize_columns(df):
    df.columns = df.columns.str.lower().str.strip()
    column_map = {}
    for standard_col, possible_names in COLUMN_MAPPING.items():
        for col in df.columns:
            if col in possible_names:
                column_map[standard_col] = col
                break
    return df.rename(columns=column_map), column_map

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

def extract_campaign_name(text):
    """Извлекает название РК из строки"""
    parts = text.lower().split("//")
    return parts[1].strip() if len(parts) > 1 else text.strip()

# Интерфейс Streamlit
st.title("Анализ качества рекламных кампаний")

# Функция для загрузки и обработки данных
def load_and_process_data(upload_option, campaign_name=None, unique_key="file_uploader_1", google_sheet_url=None):
    df = None

    if upload_option == "Загрузить Excel-файл":
        uploaded_file = st.file_uploader("Загрузите файл", type=["xlsx"], key=unique_key)
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            campaign_name = extract_campaign_name(uploaded_file.name)

    elif upload_option == "Ссылка на Google-таблицу" and google_sheet_url:
        try:
            sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
            gid = google_sheet_url.split("gid=")[1].split("&")[0] if "gid=" in google_sheet_url else "0"
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            df = pd.read_csv(csv_url)
        except Exception as e:
            st.error(f"Ошибка при загрузке CSV: {e}")

        if google_sheet_url:
            campaign_name = extract_campaign_name(google_sheet_url)

    if df is not None:
        df, col_map = process_data(df)
        st.write(f"Название РК: {campaign_name}")

        # Выбор периода
        if "дата" in col_map:
            min_date = df[col_map["дата"]].min().date()
            max_date = df[col_map["дата"]].max().date()
            start_date, end_date = st.

date_input("Выберите период", [min_date, max_date], key=f"date_input_{unique_key}")

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
            {campaign_name}
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

# Загрузка и обработка нескольких ссылок
st.header("Загрузите до 10 ссылок на Google-таблицы")

for i in range(1, 11):
    google_sheet_url = st.text_input(f"Ссылка на Google-таблицу {i}", key=f"google_sheet_url_{i}")
    if google_sheet_url:
        upload_option = "Ссылка на Google-таблицу"
        campaign_name = f"Загрузка {i}"  # Имя по умолчанию
        custom_campaign_name = st.text_input(f"Введите название РК {i} (или оставьте по умолчанию)", value=campaign_name)
        load_and_process_data(upload_option, campaign_name=custom_campaign_name, unique_key=f"file_uploader_{i}", google_sheet_url=google_sheet_url)
