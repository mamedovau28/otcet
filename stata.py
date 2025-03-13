import pandas as pd
import streamlit as st
import calendar

def find_project_name(df):
    """Ищет название проекта, проверяя сначала строку под 'проект', затем следующий столбец"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and "проект" in value.lower():
                # Проверяем строку ниже
                if idx + 1 < len(df) and isinstance(df[col][idx + 1], str):
                    if "период" not in df[col][idx + 1].lower():
                        return df[col][idx + 1].strip()
                # Проверяем следующий столбец
                next_col_idx = col_idx + 1
                if next_col_idx < len(df.columns):
                    next_col = df.columns[next_col_idx]
                    return df[next_col][idx] if isinstance(df[next_col][idx], str) else "Название проекта отсутствует"
    return "Проект не найден"

def find_period(df):
    """Находит период в таблице. Проверяет строку ниже, если есть, или следующий столбец."""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and "период" in value.lower():
                # Проверяем строку ниже
                if idx + 1 < len(df) and isinstance(df[col][idx + 1], str):
                    return df[col][idx + 1].strip()
                # Если в той же строке, но в следующем столбце есть значение – берем его
                next_col_idx = col_idx + 1
                if next_col_idx < len(df.columns):
                    next_col = df.columns[next_col_idx]
                    next_value = df[next_col][idx]
                    if isinstance(next_value, str):
                        return next_value.strip()
    return "Период не найден"

def parse_period(period_str):
    """Обрабатывает период: если это диапазон дат — оставляет, если сокращенный месяц — преобразует"""
    if not isinstance(period_str, str):
        return period_str
    period_str = period_str.strip().lower().replace(" ", "").replace("\xa0", "")  # Убираем лишние пробелы и неразрывные пробелы
    
    if "-" in period_str:
        return period_str  # Уже диапазон дат

    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }

    for month_abbr, month_num in months.items():
        # Обрабатываем формат с точкой, например "фев.25"
        if period_str.startswith(month_abbr):
            year_part = period_str[len(month_abbr):].replace('.', '').strip()  # Убираем точку и пробелы
            if len(year_part) == 2 and year_part.isdigit():
                year = int("20" + year_part)  # Двухзначный год
            elif len(year_part) == 4 and year_part.isdigit():
                year = int(year_part)  # Четырехзначный год
            else:
                return "Ошибка в формате периода"  # Если год невалиден
            last_day = calendar.monthrange(year, month_num)[1]
            return f"01.{month_num:02}.{year}-{last_day}.{month_num:02}.{year}"
    
    return "Ошибка в формате периода"  # Если формат не распознан
    
def find_table_start(df):
    """Находит координаты ячейки с '№' или 'месяц' и возвращает индекс строки и колонки"""
    for col_idx, col in enumerate(df.columns):
        for row_idx, value in df[col].items():
            if isinstance(value, str) and ("№" in value or "месяц" in value.lower()):
                return row_idx, col_idx
    return None, None

def extract_campaigns_table(df):
    """Извлекает таблицу с рекламными кампаниями, начиная с найденной строки и колонки"""
    row_idx, col_idx = find_table_start(df)
    if row_idx is not None and col_idx is not None:
        return df.iloc[row_idx:, col_idx:].reset_index(drop=True)
    return None

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта и периода
    project_name = find_project_name(df)
    period_raw = find_period(df)
    
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower():
        period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
    
    # Вывод информации о проекте
    st.subheader("Информация о проекте")
    st.success(f"Название проекта: {project_name}" if "не найден" not in project_name.lower() else project_name)
    st.success(f"Период: {period}" if "не найден" not in period.lower() else period)
    
    # Вывод таблицы рекламных кампаний
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")

