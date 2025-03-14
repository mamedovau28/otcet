> Юлия Мамедова:
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
            # Проверяем, содержит ли колонка только цифры
            if not pd.api.types.is_numeric_dtype(df[col_map[key]]):
                df[col_map[key]] = (
                    df[col_map[key]]
                    .astype(str)
                    .str.replace(r"[^\d]", "", regex=True)  # Оставляем только цифры
                )
                df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)  # Преобразуем в числа

    df[col_map["расход"]] = df[col_map["расход"]] / 100

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

def extract_campaign_name_from_gid(url):
    """Извлекает название РК из gid Google Sheets URL"""
    try:
        gid = url.split("gid=")[1].split("&")[0]
        return f"Campaign {gid}"  # Название РК на основе gid
    except Exception:
        return "Unknown Campaign"

# Интерфейс Streamlit
st.title("Анализ качества рекламных кампаний")

upload_option = st.radio("Выберите способ загрузки данных статистики по площадкам:", ["Загрузить Excel-файлы", "Ссылки на Google-таблицы"])

dfs = []  # Список для хранения данных из нескольких файлов
campaign_names = []  # Список для хранения названий РК

if upload_option == "Загрузить Excel-файлы":
    uploaded_files = st.file_uploader("Загрузите файлы", type=["xlsx"], accept_multiple_files=True)
    if uploaded_files:
        for uploaded_file in uploaded_files:
            df = pd.read_excel(uploaded_file)
            dfs.append(df)
            campaign_name = extract_campaign_name_from_gid(uploaded_file.name)
            campaign_names.append(campaign_name)

elif upload_option == "Ссылки на Google-таблицы":
    google_sheet_urls = st.text_area("Введите ссылки на Google-таблицы (каждая ссылка с новой строки)").splitlines()
    if google_sheet_urls:
        for google_sheet_url in google_sheet_urls:
            try:
                csv_url = f"https://docs.google.com/spreadsheets/d/{google_sheet_url.split('/d/')[1].split('/')[0]}/export?format=csv&gid={google_sheet_url.split('gid=')[1].split('&')[0]}"
                df = pd.read_csv(csv_url)
                dfs.append(df)
                campaign_name = extract_campaign_name_from_gid(google_sheet_url)
