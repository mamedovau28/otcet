import streamlit as st
import pandas as pd

# Добавим "расход до ндс" в варианты для столбца "расход"
COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс"],
    "охват": ["охват", "reach"]
}

def standardize_columns(df):
    """
    Приводим названия колонок к нижнему регистру и ищем нужные столбцы
    на основе словаря COLUMN_MAPPING.
    """
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
    - Убираем 'p.' или 'p' (если есть).
    - Удаляем пробелы.
    - Заменяем запятую на точку.
    - Пробуем привести к float.
    - При ошибке возвращаем 0.
    """
    if isinstance(x, str):
        # Убираем 'p.' или 'p' (если вдруг есть)
        x = x.replace('p.', '').replace('p', '')
        # Удаляем пробелы
        x = x.replace(' ', '')
        # Заменяем запятую на точку
        x = x.replace(',', '.')
        try:
            return float(x)
        except:
            return 0.0
    else:
        # Если это уже число, просто вернём как есть
        return float(x)

def process_data(df):
    """
    Приводит столбцы к нужным названиям, чистит данные,
    считает Расход с НДС, пересчитывает охват (если %),
    считает CTR (учитывая деление на 0).
    """
    df, col_map = standardize_columns(df)
    df.fillna(0, inplace=True)

    # Парсим дату, если есть соответствующий столбец
    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    # Если есть столбец "расход", парсим значения и считаем с НДС
    if "расход" in col_map:
        # Преобразуем исходные значения (убираем 'p.', пробелы, запятые и т.д.)
        df[col_map["расход"]] = df[col_map["расход"]].apply(parse_cost_value)
        # Добавляем расчет с НДС
        df["расход с ндс"] = df[col_map["расход"]] * 1.2

    # Пересчитываем охват, если он в процентах (например, "0,20%")
    if "охват" in col_map and "показы" in col_map:
        df["охват"] = df.apply(
            lambda row: row[col_map["показы"]] * (
                float(str(row[col_map["охват"]]).replace("%", "").replace(",", ".")) / 100
            ) if isinstance(row[col_map["охват"]], str) and "%" in row[col_map["охват"]] else row[col_map["охват"]],
            axis=1
        )

    # Считаем CTR: клики / показы (если показы > 0)
    if "клики" in col_map and "показы" in col_map:
        df["ctr"] = df.apply(
            lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] else 0,
            axis=1
        )

    return df, col_map

def extract_campaign_name(filename):
    """
    Извлекает название РК, клиента и проекта из имени файла.
    Формат: ARWM // OneTarget // Sminex // Dom-Dostigenie
    Если встречаем 'arwm' (в любом регистре) в начале, пропускаем его.
    """
    parts = filename.lower().split(" // ")
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
        # Извлекаем ID таблицы
        sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
        # Формируем ссылку для получения CSV
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(url)
        campaign_name, client_name, project_name = extract_campaign_name(google_sheet_url)

if df is not None:
    st.write(f"### {campaign_name} | {client_name} | {project_name}")

    df, col_map = process_data(df)

    # Если есть дата - даём выбрать период
    if "дата" in col_map:
        min_date = df[col_map["дата"]].min()
        max_date = df[col_map["дата"]].max()
        start_date, end_date = st.date_input("Выберите период", [min_date, max_date])

        # Фильтруем
        df_filtered = df[
            (df[col_map["дата"]] >= pd.to_datetime(start_date)) &
            (df[col_map["дата"]] <= pd.to_datetime(end_date))
        ]

        # Суммируем
        # Обратите внимание, что dataframe может не содержать все нужные колонки
        # поэтому перед суммированием проверим, есть ли они
        cols_for_summary = []
        for c in ["показы", "клики", "охват", "расход с ндс"]:
            if c in df_filtered.columns:
                cols_for_summary.append(c)

        summary = df_filtered[cols_for_summary].sum()

        st.write("### Итоговый отчёт")
        st.write(f"**{campaign_name}**")
        st.write(f"**{client_name}**")

        # Показы
        total_impressions = summary.get("показы", 0)
        st.write(f"Показы: {total_impressions:.0f}")

        # Клики
        total_clicks = summary.get("клики", 0)
        st.write(f"Клики: {total_clicks:.0f}")

        # CTR
        ctr_value = 0
        if total_impressions > 0:
            ctr_value = total_clicks / total_impressions
        st.write(f"CTR: {ctr_value:.2%}")

        # Охват
        total_reach = summary.get("охват", 0)
        st.write(f"Охват: {total_reach:.0f}")

        # Расход с НДС
        total_spend_nds = summary.get("расход с ндс", 0)
        st.write(f"Расход с НДС: {total_spend_nds:.2f} руб.")

    # Выводим обработанный датафрейм
    st.dataframe(df)
