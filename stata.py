import pandas as pd
import streamlit as st
import calendar

def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Ищет строку с нужным словом и берет значение из следующего столбца"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and keyword in value.lower():
                next_col_idx = col_idx + 1
                if next_col_idx < len(df.columns):
                    next_col = df.columns[next_col_idx]
                    return df[next_col][idx]
                else:
                    return empty_msg
    return not_found_msg

def find_project_name(df):
    """Находит название проекта. Если под 'проект' указано 'период', берет название из следующего столбца"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and "проект" in value.lower():
                next_row_idx = idx + 1
                if next_row_idx < len(df):
                    next_row_value = df[col][next_row_idx]
                    if isinstance(next_row_value, str) and "период" in next_row_value.lower():
                        next_col_idx = col_idx + 1
                        if next_col_idx < len(df.columns):
                            next_col = df.columns[next_col_idx]
                            return df[next_col][idx]
                        else:
                            return "Название проекта отсутствует"
                    return next_row_value
    return "Проект не найден"

def parse_period(period_str):
    """
    Преобразует период, заданный в сокращенном формате.
    Если период содержит "-", считаем, что это уже диапазон дат и возвращаем его как есть.
    Если период вида "фев.25" или "фев.2025", то он преобразуется в формат:
    "01.MM.YYYY-last_day.MM.YYYY", где last_day – последний день месяца.
    """
    if not isinstance(period_str, str):
        return period_str
    period_str = period_str.strip().lower().replace(" ", "")

    if "-" in period_str:
        return period_str

    # Русские аббревиатуры месяцев
    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6, "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }
    
    for abbr, month in months.items():
        if period_str.startswith(abbr):
            year_part = period_str[len(abbr):]
            if len(year_part) == 2:
                year = int("20" + year_part)
            elif len(year_part) == 4:
                year = int(year_part)
            else:
                return "Период не найден"
            last_day = calendar.monthrange(year, month)[1]
            return f"01.{month:02}.{year}-{last_day}.{month:02}.{year}"
    return "Период не найден"

def find_table_start(df):
    """Находит координаты ячейки с '№' или 'месяц' и возвращает индекс строки и колонки"""
    for col_idx, col in enumerate(df.columns):
        for row_idx, value in df[col].items():
            if isinstance(value, str):
                if "№" in value or "месяц" in value.lower():
                    return row_idx, col_idx
    return None, None  

def extract_campaigns_table(df):
    """Извлекает таблицу с рекламными кампаниями, начиная с найденной строки и колонки"""
    row_idx, col_idx = find_table_start(df)
    if row_idx is not None and col_idx is not None:
        return df.iloc[row_idx:, col_idx:]
    return None

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта
    project_name = find_project_name(df)
    
    # Поиск периода
    period_raw = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")
    period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
# Вывод информации о проекте
    st.subheader("Информация о проекте")
    if project_name.startswith("Проект не найден") or project_name.startswith("Название проекта отсутствует"):
        st.warning(project_name)
    else:
        st.success(f"Название проекта: {project_name}")
    
    if period.startswith("Период не найден") or period.startswith("Период отсутствует"):
        st.warning(period)
    else:
        st.success(f"Период: {period}")

    # Вывод таблицы рекламных кампаний
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")
