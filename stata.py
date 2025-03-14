import streamlit as st
import pandas as pd
import re
import requests

# Словарь для сопоставления названий колонок
COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс"],
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

def parse_cost_value(x):
    """
    Преобразует строку вида 'p.10 673,98' в число:
    - Удаляет все символы, кроме цифр, точки и запятой,
    - Заменяет запятую на точку,
    - Преобразует в float.
    """
    if isinstance(x, str):
        x = re.sub(r'[^0-9,\.]', '', x)
        x = x.replace(',', '.')
        try:
            return float(x)
        except:
            return 0.0
    else:
        try:
            return float(x)
        except:
            return 0.0

def process_data(df):
    df, col_map = standardize_columns(df)
    df.fillna(0, inplace=True)

    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    if "расход" in col_map:
        df[col_map["расход"]] = df[col_map["расход"]].apply(parse_cost_value)
        df["расход с ндс"] = df[col_map["расход"]] * 1.2

    if "охват" in col_map and "показы" in col_map:
        df["охват"] = df.apply(
            lambda row: row[col_map["показы"]] * (
                float(str(row[col_map["охват"]]).replace("%", "").replace(",", "."))
            ) / 100 if isinstance(row[col_map["охват"]], str) and "%" in row[col_map["охват"]]
            else row[col_map["охват"]],
            axis=1
        )

    if "клики" in col_map and "показы" in col_map:
        df["ctr"] = df.apply(
            lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] > 0 else 0,
            axis=1
        )

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
