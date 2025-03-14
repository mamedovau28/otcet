import streamlit as st
import pandas as pd
import re

# Словари для сопоставления названий колонок
COLUMN_MAPPING = {
    "площадка": ["площадка", "сайт", "ресурс", "название сайта"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "охват": ["охват", "reach"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"]
}

def standardize_columns(df):
    """Приводит названия колонок к стандартному виду"""
    df.columns = df.columns.astype(str).str.lower().str.strip()
    column_map = {}
    for standard_col, possible_names in COLUMN_MAPPING.items():
        for col in df.columns:
            # Проверяем, что хотя бы одно слово из возможных вариантов содержится в названии столбца
            if any(word in col for word in possible_names):
                column_map[standard_col] = col
                break
    return df.rename(columns=column_map), column_map

def clean_mp(mp_df):
    """
    Ищем первую строку, в которой встречается слово "площадка" (без учета регистра).
    Считаем эту строку заголовочной и возвращаем таблицу начиная с этой строки.
    """
    for i, row in mp_df.iterrows():
        # Преобразуем значения строки в строки и ищем слово "площадка"
        if row.astype(str).str.contains("площадка", case=False, na=False).any():
            # Возьмем таблицу начиная с найденной строки
            mp_df = mp_df.iloc[i:].reset_index(drop=True)
            # Сделаем первую строку заголовками
            mp_df.columns = mp_df.iloc[0]
            mp_df = mp_df[1:].reset_index(drop=True)
            return mp_df
    return None

def process_mp(mp_df):
    """Обрабатывает медиаплан: ищет нужную таблицу, оставляет нужные столбцы и фильтрует строки."""
    mp_df = clean_mp(mp_df)
    if mp_df is None:
        st.error("Ошибка: не удалось найти строку с заголовками, содержащую слово 'площадка'.")
        return None

    mp_df, col_map = standardize_columns(mp_df)

    # Обязательные столбцы
    required_cols = {"площадка", "показы", "клики"}
    missing_columns = [col for col in required_cols if col not in col_map]
    if missing_columns:
        st.error(f"Отсутствуют обязательные столбцы: {', '.join(missing_columns)}")
        return None

    # Выбираем только нужные столбцы (охват необязателен)
    selected_cols = list(required_cols)
    if "охват" in col_map:
        selected_cols.append("охват")

    # Извлекаем данные только из выбранных столбцов
    mp_df = mp_df[[col_map[col] for col in selected_cols if col in col_map]]

    # Удаляем строки, где обязательные столбцы не заполнены
    mp_df.dropna(subset=[col_map["площадка"], col_map["показы"], col_map["клики"]], how="any", inplace=True)

    st.write("Обработанный медиаплан:")
    st.dataframe(mp_df)
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
