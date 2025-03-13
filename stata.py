import pandas as pd
import streamlit as st
import calendar
import re

# Функция для преобразования периода
def parse_period(period_str):
    """
    Преобразует период в формат "01.MM.YYYY-last_day.MM.YYYY".
    Если строка уже в таком формате (например, "01.01.2025"), то она просто возвращается.
    Если период задан как сокращение месяца (например, "фев.25"), то преобразуется в формат "01.02.2025-28.02.2025".
    """
    if not isinstance(period_str, str):
        return period_str

    period_str = period_str.strip().lower().replace(" ", "")
    
    # Проверка на диапазон дат (например, "01.01.2025-31.01.2025")
    if "-" in period_str:
        return period_str

    # Проверка, является ли строка датой в формате "01.01.2025"
    date_pattern = r"^\d{2}\.\d{2}\.\d{4}$"
    if re.match(date_pattern, period_str):
        # Если строка в формате даты, возвращаем её как период
        return period_str
    
    # Словарь с месяцами на русском языке
    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6, "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }

    # Ищем, с каким месяцем начинается строка
    for abbr, month in months.items():
        if period_str.startswith(abbr):
            # Остаток строки — это год
            year_part = period_str[len(abbr):]  # остаток строки
            if len(year_part) == 2:  # если это 2 цифры, то это 20xx
                year = int("20" + year_part)
            elif len(year_part) == 4:  # если 4 цифры, это полный год
                year = int(year_part)
            else:
                return period_str  # если год не корректный, возвращаем строку как есть
            
            # Получаем последний день месяца
            last_day = calendar.monthrange(year, month)[1]
            # Формируем период с первым и последним днем месяца
            return f"01.{month:02}.{year}-{last_day}.{month:02}.{year}"

    # Если это не период в нужном формате, возвращаем строку как есть
    return period_str

# Функция для поиска значений по ключевому слову в таблице
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

# Функция для поиска месяца в таблице
def find_month_in_table(df, month_abbrs):
    """Ищет месяц в таблице и возвращает строку с рекламным месяцем"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str):
                for abbr in month_abbrs:
                    if abbr in value.lower():
                        # Пытаемся найти значение периода, которое будет на строке ниже
                        st.write(f"Найден месяц: {abbr}, строка: {value}, индекс: {idx}")
                        return df.iloc[idx+1:]  # Возвращаем строки после найденного месяца
    return None

# Функция для поиска координат таблицы по ключевым словам
def find_table_start(df):
    """Находит координаты ячейки с '№' или 'месяц' и возвращает индекс строки и колонки"""
    for col_idx, col in enumerate(df.columns):
        for row_idx, value in enumerate(df[col].items()):
            if isinstance(value, str):
                if "№" in value or "месяц" in value.lower():
                    return row_idx, col_idx  # Возвращаем строку и колонку, где нашли "№" или "месяц"
    return None, None  

# Функция для извлечения таблицы с рекламными кампаниями
def extract_campaigns_table(df):
    """Извлекает таблицу с рекламными кампаниями, начиная с найденной строки и колонки"""
    row_idx, col_idx = find_table_start(df)
    if row_idx is not None and col_idx is not None:
        st.write(f"Таблица начинается с строки {row_idx}, колонки {col_idx}")
        return df.iloc[row_idx:, col_idx:]
    return None

# Основной код для загрузки файла и обработки данных
st.title("Обработка данных рекламных кампаний")

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта и периода
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    period_raw = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")
    
    # Преобразование периода
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower():
        # Преобразуем период, если это строка, а не ошибка
        period = parse_period(period_raw)
    
    # Если период не найден, ищем месяц в таблице
    if period == "Период не найден":
        months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
        campaigns_table = find_month_in_table(df, months)
        if campaigns_table is not None:
            # Находим строку с рекламным месяцем
            st.success("Рекламный месяц найден!")
        else:
            st.warning("Месяц не найден!")
    
    # Вывод информации о проекте
    st.subheader("Информация о проекте")
    if project_name.startswith("Проект не найден") or project_name.startswith("Название проекта отсутствует"):
        st.warning(project_name)
    else:
        st.success(f"Название проекта: {project_name}")
    
    if isinstance(period, str) and (period.startswith("Период не найден") or period.startswith("Период отсутствует")):
        st.warning(period)
    else:
        st.success(f"Период: {period}")

    # Вывод таблицы рекламных кампаний
    campaigns_table = extract_campaigns_table(df)
    if campaigns_table is not None:
        st.subheader("Таблица рекламных кампаний")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена.")
