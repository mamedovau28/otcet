import streamlit as st
import pandas as pd

# Словарь для поиска нужных колонок
COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд"],
    "охват": ["охват", "reach"]
}

# Функция для приведения названий колонок к единому формату
def standardize_columns(df):
    df.columns = df.columns.str.lower().str.strip()  # Приводим к нижнему регистру и убираем пробелы
    column_map = {}  # Словарь соответствий
    
    for standard_col, possible_names in COLUMN_MAPPING.items():
        for col in df.columns:
            if col in possible_names:
                column_map[standard_col] = col
                break  # Берем первое совпадение

    return df.rename(columns=column_map), column_map

# Функция для извлечения названия РК, клиента и проекта
def extract_campaign_name(filename):
    parts = filename.lower().split(" // ")
    if len(parts) >= 4 and parts[0] == "arwm":
        return parts[1], parts[2], parts[3]  # Площадка, клиент, проект
    return None, None, None

# Функция обработки данных
def process_data(df):
    df, col_map = standardize_columns(df)  # Приводим названия колонок к стандарту

    # Очистка данных (замена пустых значений на 0)
    df.fillna(0, inplace=True)

    # Преобразуем даты
    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    # Добавляем расчет расхода с НДС
    if "расход" in col_map:
        df["расход с ндс"] = df[col_map["расход"]] * 1.2

    # Пересчитываем охват, если он в процентах
    if "охват" in col_map and "показы" in col_map:
        df["охват"] = df.apply(
            lambda row: row[col_map["показы"]] * (float(str(row[col_map["охват"]]).replace("%", "").replace(",", ".")) / 100)
            if isinstance(row[col_map["охват"]], str) and "%" in row[col_map["охват"]]
            else row[col_map["охват"]],
            axis=1
        )

    # Рассчитываем CTR
    if "клики" in col_map and "показы" in col_map:
        df["ctr"] = df[col_map["клики"]] / df[col_map["показы"]]

    return df, col_map

# Интерфейс Streamlit
st.title("Анализ качества рекламных кампаний")

# Выбор способа загрузки данных
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
        sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]  # Извлекаем ID таблицы
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(url)
        campaign_name, client_name, project_name = extract_campaign_name(google_sheet_url)

# Если данные загружены, обрабатываем их
if df is not None:
    st.write(f"### {campaign_name} | {client_name} | {project_name}")

    df, col_map = process_data(df)

    # Выбор периода
    if "дата" in col_map:
        min_date, max_date = df[col_map["дата"]].min(), df[col_map["дата"]].max()
        start_date, end_date = st.date_input("Выберите период", [min_date, max_date])
        
        # Фильтруем данные по периоду
        df_filtered = df[(df[col_map["дата"]] >= pd.to_datetime(start_date)) & (df[col_map["дата"]] <= pd.to_datetime(end_date))]

        # Суммируем данные за выбранный период
        summary = df_filtered[["показы", "клики", "охват", "расход с ндс"]].sum()

        # Выводим отчёт
        st.write("### Итоговый отчёт")
        st.write(f"**{campaign_name}**")
        st.write(f"**{client_name}**")
        st.write(f"Показы: {summary['показы']:.0f}")
        st.write(f"Клики: {summary['клики']:.0f}")
        st.write(f"CTR: {summary['клики'] / summary['показы']:.2%}")
        st.write(f"Охват: {summary['охват']:.0f}")
        st.write(f"Расход с НДС: {summary['расход с ндс']:.2f} руб.")

    # Показываем обработанную таблицу
    st.dataframe(df)
