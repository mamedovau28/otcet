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

def parse_period(period_str):
    """Обрабатывает период: если это диапазон дат — оставляет, если сокращенный месяц — преобразует"""
    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }
    
    if isinstance(period_str, str):
        period_str = period_str.replace(" ", "").lower()  # Убираем пробелы и приводим к нижнему регистру
        
        # Проверяем, является ли это диапазоном дат (например, 01.01.2025-01.02.2025)
        if "-" in period_str and len(period_str.split("-")) == 2:
            return period_str  # Уже диапазон дат, возвращаем как есть

        # Проверяем, является ли это сокращенным месяцем (например, фев.25 или фев.2025)
        for month_abbr, month_num in months.items():
            if period_str.startswith(month_abbr):
                year_part = period_str[len(month_abbr):]  # Берем часть строки после месяца
                if year_part.isdigit():
                    year = int("20" + year_part) if len(year_part) == 2 else int(year_part)  # Приводим год к 2025 формату
                    last_day = calendar.monthrange(year, month_num)[1]  # Определяем последний день месяца
                    return f"01.{month_num:02}.{year} - {last_day}.{month_num:02}.{year}"

    return period_str  # Если не смогли обработать, оставляем как есть

def find_table_start(df):
    """Находит координаты ячейки с '№' или 'месяц' и возвращает индекс строки и колонки"""
    for col_idx, col in enumerate(df.columns):
        for row_idx, value in df[col].items():
            if isinstance(value, str):
                if "№" in value or "месяц" in value.lower():
                    return row_idx, col_idx  # Возвращаем строку и колонку, где нашли "№" или "месяц"
    return None, None  

def extract_campaigns_table(df):
    """Извлекает таблицу с рекламными кампаниями, начиная с найденной строки и колонки"""
    row_idx, col_idx = find_table_start(df)
    if row_idx is not None and col_idx is not None:
        table_data = df.iloc[row_idx:, col_idx:].copy()

        # Преобразуем первую строку в заголовки
        table_data.columns = table_data.iloc[0]
        table_data = table_data[1:].reset_index(drop=True)

        # Если есть столбец 'месяц', удаляем строки, где он пустой
        month_col = next((col for col in table_data.columns if isinstance(col, str) and "месяц" in col.lower()), None)
        if month_col:
            table_data = table_data.dropna(subset=[month_col])

        return table_data
    return None  

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)  
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))  
    df = df[sheet_name]  
    
    # Поиск проекта и периода
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    period = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")

    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)

    # Вывод проекта и периода
    st.subheader("Информация о проекте")
    if project_name.startswith("Проект не найден") or project_name.startswith("Название проекта отсутствует"):
        st.warning(project_name)
    else:
        st.success(f"Название проекта: {project_name}")

    if period.startswith("Период не найден") or period.startswith("Период отсутствует"):
        st.warning(period)
    else:
        st.success(f"Период: {period}")

    # Вывод таблицы с рекламными кампаниями
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")
