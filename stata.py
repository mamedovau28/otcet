import pandas as pd
import streamlit as st
import calendar

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
        # Если это диапазон дат, возвращаем без изменений.
        return period_str

    # Русские аббревиатуры месяцев
    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6, "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }
    # Ищем, с каким месяцем начинается строка
    for abbr, month in months.items():
        if period_str.startswith(abbr):
            year_part = period_str[len(abbr):]  # остаток строки – год
            if len(year_part) == 2:
                year = int("20" + year_part)
            elif len(year_part) == 4:
                year = int(year_part)
            else:
                return period_str  # если год задан некорректно, возвращаем исходное значение
            last_day = calendar.monthrange(year, month)[1]
            return f"01.{month:02}.{year}-{last_day}.{month:02}.{year}"
    return period_str
    
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
    
def find_table_start(df):
    """Находит координаты ячейки с '№' или 'месяц' и возвращает индекс строки и колонки"""
    for col_idx, col in enumerate(df.columns):
        for row_idx, value in df[col].items():
            if isinstance(value, str):
                if "№" in value or "месяц" in value.lower():
                    return row_idx, col_idx  # Возвращаем строку и колонку, где нашли "№" или "месяц"
    return None, None 
    
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
    
     # Проверка на наличие фразы "не найден" и последующее преобразование периода
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower() and "сезонныйкоэффициент" not in period_raw.lower():
        period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
    
    # Вывод информации о проекте
    st.subheader("Информация о проекте")
    st.success(f"Название проекта: {project_name}" if "не найден" not in project_name.lower() else project_name)
    st.success(f"Период: {period}")
    
    # Вывод таблицы рекламных кампаний
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")

