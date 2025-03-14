import streamlit as st
import pandas as pd
import re
import requests

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

    # Преобразование показов и кликов
    if "клики" in col_map and "показы" in col_map and "охват" in col_map and "расход" in col_map:
        for key in ["показы", "клики", "охват", "расход"]:
            df[col_map[key]] = df[col_map[key]].astype(str).str.replace(r"[^\d]", "", regex=True)  # Удаляем пробелы и лишние символы
            df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)  # Преобразуем в числа
            df[col_map[key]] = df[col_map[key]] / 10

    df[col_map["расход"]] = df[col_map["расход"]] / 10

    if "охват" in col_map and "показы" in col_map:
        def adjust_coverage(row):
            coverage = row[col_map["охват"]]
            impressions = row[col_map["показы"]]

            if coverage > 0 and impressions > 0:
                if impressions / coverage > 10:  # Если показы в 10 раз больше охвата
                    return impressions * (coverage / 100)  # Пересчитываем охват
            return coverage  # Оставляем как есть

        df["охват"] = df.apply(adjust_coverage, axis=1)
            
    return df, col_map
    
def extract_campaign_name(text):
    """
    Извлекает название РК, клиента и проекта из строки формата:
    ARWM // OneTarget // Sminex // Dom-Dostigenie.
    Если встречается 'arwm' в начале – пропускаем его.
    """
    parts = text.lower().split(" // ")
    if len(parts) >= 4 and parts[0] == "arwm":
        return parts[1], parts[2], parts[3]
    return None, None, None

# --------------------------- Интерфейс Streamlit ---------------------------
st.title("Анализ качества рекламных кампаний")

upload_option = st.radio("Выберите способ загрузки данных:", ["Загрузить Excel-файл", "Ссылка на Google-таблицу"])

df = None
campaign_name = client_name = project_name = None

if upload_option == "Загрузить Excel-файл":
    uploaded_file = st.file_uploader("Загрузите файл", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        campaign_name, client_name, project_name = extract_campaign_name(uploaded_file.name)

elif upload_option == "Ссылка на Google-таблицу":
    google_sheet_url = st.text_input("Введите ссылку на Google-таблицу")
    if google_sheet_url:
        try:
            # Извлекаем sheet_id из ссылки
            sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
            # Извлекаем gid из ссылки
            if "gid=" in google_sheet_url:
                gid = google_sheet_url.split("gid=")[1].split("&")[0]
            else:
                gid = "0"  # дефолтное значение
        except IndexError:
            st.error("Неверный формат ссылки.")
            sheet_id = None

        if sheet_id:
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            try:
                df = pd.read_csv(csv_url)
            except Exception as e:
                st.error(f"Ошибка при загрузке CSV: {e}")

# Если название РК не извлекается из ссылки, предлагаем ввести вручную
        manual_name = st.text_input("Введите название РК (например: 'ARWM // OneTarget // Sminex // Dom-Dostigenie')")
        if manual_name:
            campaign_name, client_name, project_name = extract_campaign_name(manual_name)

if df is not None:
    st.write(f"### {campaign_name} | {client_name} | {project_name}")
    df, col_map = process_data(df)

    # Если присутствует столбец с датой, даем выбрать период
    if "дата" in col_map:
        min_date = df[col_map["дата"]].min()
        max_date = df[col_map["дата"]].max()
        start_date, end_date = st.date_input("Выберите период", [min_date, max_date])
        df_filtered = df[
            (df[col_map["дата"]] >= pd.to_datetime(start_date)) &
            (df[col_map["дата"]] <= pd.to_datetime(end_date))
        ]

        needed_cols = ["показы", "клики", "охват", "расход с ндс"]
        existing_cols = [col for col in needed_cols if col in df_filtered.columns]
        summary = df_filtered[existing_cols].sum()

        st.write("### Итоговый отчёт")
        st.write(f"**{campaign_name}**")
        st.write(f"**{client_name}**")

        total_impressions = summary.get("показы", 0)
        st.write(f"Показы: {total_impressions:.0f}")

        total_clicks = summary.get("клики", 0)
        st.write(f"Клики: {total_clicks:.0f}")

        ctr_value = total_clicks / total_impressions if total_impressions > 0 else 0
        st.write(f"CTR: {ctr_value:.2%}")

        total_reach = summary.get("охват", 0)
        st.write(f"Охват: {total_reach:.0f}")

        total_spend_nds = summary.get("расход с ндс", 0)
        st.write(f"Расход с НДС: {total_spend_nds:.2f} руб.")

    st.dataframe(df)
