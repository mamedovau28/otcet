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
        > Юлия Мамедова:
AttributeError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).Traceback:^File "/mount/src/otcet/stata.py", line 13, in find_value_by_keyword
    if "период" in next_row_value.lower():  # Если в строке ниже есть слово "период"
                   ^^^^^^^^^^^^^^^^^^^^

> Юлия Мамедова:
import pandas as pd
import streamlit as st
import calendar

def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Ищет строку с нужным словом и берет значение из следующего столбца"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and keyword in value.lower():
                # Проверяем строку ниже по текущему столбцу
                if idx + 1 < len(df):
                    next_row_value = df[col][idx + 1]
                    if isinstance(next_row_value, str) and "период" in next_row_value.lower():  # Проверка типа и наличия слова "период"
                        # Ищем название проекта в следующем столбце
                        next_col_idx = col_idx + 1  
                        if next_col_idx < len(df.columns):
                            next_col = df.columns[next_col_idx]
                            return df[next_col][idx]
                        else:
                            return empty_msg
                    elif isinstance(next_row_value, str):  # Если в строке ниже нет "периода", но это строка, считаем это название проекта
                        return next_row_value
                else:
                    return empty_msg  # Если ниже нет строки
    return not_found_msg  # Если не нашли "проект"

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
        return df.iloc[row_idx:, col_idx:]
    return None

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта и периода
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    period_raw = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")
    
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.

> Юлия Мамедова:
lower() and "отсутствует" not in period_raw.lower():
        period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
    
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
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")

> Юлия Мамедова:
import pandas as pd
import streamlit as st
import calendar

def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Ищет строку с нужным словом и берет значение из следующего столбца"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and keyword in value.lower():
                # Проверяем строку ниже по текущему столбцу
                if idx + 1 < len(df):
                    next_row_value = df[col][idx + 1]
                    if isinstance(next_row_value, str) and "период" in next_row_value.lower():  # Проверка типа и наличия слова "период"
                        # Ищем название проекта в следующем столбце
                        next_col_idx = col_idx + 1  
                        if next_col_idx < len(df.columns):
                            next_col = df.columns[next_col_idx]
                            return df[next_col][idx]
                        else:
                            return empty_msg
                    elif isinstance(next_row_value, str):  # Если в строке ниже нет "периода", но это строка, считаем это название проекта
                        return next_row_value
                else:
                    return empty_msg  # Если ниже нет строки
    return not_found_msg  # Если не нашли "проект"

def find_period(df):
    """Находит период, проверяя строку под 'период' и возвращает значение"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and "период" in value.lower():
                if idx + 1 < len(df):
                    next_row_value = df[col][idx + 1]
                    return next_row_value  # Возвращаем значение из следующей строки
    return "Период не найден"  # Если не нашли период

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
        return df.iloc[row_idx:, col_idx:]
    return None

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.

> Юлия Мамедова:
read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    
    # Поиск периода
    period_raw = find_period(df)
    
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower() and "отсутствует" not in period_raw.lower():
        period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
    
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
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")

> Юлия Мамедова:
import pandas as pd
import streamlit as st
import calendar

def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Ищет строку с нужным словом и берет значение из следующего столбца"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and keyword in value.lower():
                # Проверяем строку ниже по текущему столбцу
                if idx + 1 < len(df):
                    next_row_value = df[col][idx + 1]
                    if isinstance(next_row_value, str) and "период" in next_row_value.lower():  # Проверка типа и наличия слова "период"
                        # Ищем название проекта в следующем столбце
                        next_col_idx = col_idx + 1  
                        if next_col_idx < len(df.columns):
                            next_col = df.columns[next_col_idx]
                            return df[next_col][idx]
                        else:
                            return empty_msg
                    elif isinstance(next_row_value, str):  # Если в строке ниже нет "периода", но это строка, считаем это название проекта
                        return next_row_value
                else:
                    return empty_msg  # Если ниже нет строки
    return not_found_msg  # Если не нашли "проект"

def find_period(df):
    """Находит период, проверяя строку под 'период' и возвращает значение"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and "период" in value.lower():
                # Ищем период в строке ниже, если он есть
                if idx + 1 < len(df):
                    next_row_value = df[col][idx + 1]
                    if isinstance(next_row_value, str):  # Если строка не пустая
                        return next_row_value.strip()
    return "Период не найден"  # Если не нашли период

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
        return df.iloc[row_idx:, col_idx:]
    return None

st.title("Обработка данных рекламных кампаний")

> Юлия Мамедова:
uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    
    # Поиск периода
    period_raw = find_period(df)
    
    # Если период найден, парсим его в нужный формат
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower() and "отсутствует" not in period_raw.lower():
        period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
    
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
    st.subheader("Таблица рекламных кампаний")
    if campaigns_table is not None:
        st.success("Таблица рекламных кампаний найдена:")
        st.dataframe(campaigns_table)
    else:
        st.warning("Таблица рекламных кампаний не найдена")

> Юлия Мамедова:
Просмотри код и пойми что с ним может быть не так? Сейчас период не найден

> Юлия Мамедова:
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

> Юлия Мамедова:
рабочий код!!!

> Юлия Мамедова:
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
    period_str = period_str.strip().lower().replace(" ", "")
    
    if "-" in period_str:
        return period_str  # Уже диапазон дат

    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }
    
    for month_abbr, month_num in months.items():
        if period_str.startswith(month_abbr):
            year_part = period_str[len(month_abbr):]
            if len(year_part) == 2:
                year = int("20" + year_part)
            elif len(year_part) == 4:
                year = int(year_part)
            else:
                return period_str
            last_day = calendar.monthrange(year, month_num)[1]
            return f"01.{month_num:02}.{year}-{last_day}.{month_num:02}.{year}"
    return period_str

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

> Юлия Мамедова:
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

> Юлия Мамедова:
def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Ищет строку с нужным словом и берет значение из следующего столбца"""
    for col_idx, col in enumerate(df.columns):
        for idx, value in df[col].items():
            if isinstance(value, str) and keyword in value.lower():
                next_col_idx = col_idx + 1
                if next_col_idx < len(df.columns):
                    next_col_value = df.iloc[idx, next_col_idx]
                    # Проверяем, что найденное значение не содержит посторонних слов (например, "Сезонный коэффициент")
                    if isinstance(next_col_value, str) and any(x in next_col_value.lower() for x in ["сезонный", "коэффициент"]):
                        continue  # Пропускаем такие строки
                    return next_col_value
                else:
                    return empty_msg
    return not_found_msg

> Юлия Мамедова:
база

> Юлия Мамедова:
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
    period_str = period_str.strip().lower().replace(" ", "")
    
    if "-" in period_str:
        return period_str  # Уже диапазон дат

    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }
    
    for month_abbr, month_num in months.items():
        if period_str.startswith(month_abbr):
            year_part = period_str[len(month_abbr):]
            if len(year_part) == 2:
                year = int("20" + year_part)
            elif len(year_part) == 4:
                year = int(year_part)
            else:
                return period_str
            last_day = calendar.monthrange(year, month_num)[1]
            return f"01.{month_num:02}.{year}-{last_day}.{month_num:02}.{year}"
    return period_str

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

> Юлия Мамедова:
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

> Юлия Мамедова:
def parse_period(period_str):
    """Обрабатывает период: если это диапазон дат — оставляет, если сокращенный месяц — преобразует"""
    if not isinstance(period_str, str):
        return period_str
    period_str = period_str.strip().lower().replace(" ", "")
    
    if "-" in period_str:
        return period_str  # Уже диапазон дат

    months = {
        "янв": 1, "фев": 2, "мар": 3, "апр": 4, "май": 5, "июн": 6,
        "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12
    }
    
    for month_abbr, month_num in months.items():
        if period_str.startswith(month_abbr):
            year_part = period_str[len(month_abbr):]
            if len(year_part) == 2:
                year = int("20" + year_part)
            elif len(year_part) == 4:
                year = int(year_part)
            else:
                return period_str
            last_day = calendar.monthrange(year, month_num)[1]
            return f"01.{month_num:02}.{year}-{last_day}.{month_num:02}.{year}"
    return period_str
    
    # Поиск проекта и периода
    project_name = find_project_name(df)
    period_raw = find_period(df)
    
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower():
        period = parse_period(period_raw)

> Юлия Мамедова:
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
        if period_str.startswith(month_abbr):
            year_part = period_str[len(month_abbr):].strip()
            if len(year_part) == 2 and year_part.isdigit():
                year = int("20" + year_part)
            elif len(year_part) == 4 and year_part.isdigit():
                year = int(year_part)
            else:
                return "Ошибка в формате периода"  # Добавляем защиту от неправильных данных
            last_day = calendar.monthrange(year, month_num)[1]
            return f"01.{month_num:02}.{year}-{last_day}.{month_num:02}.{year}"
    
    return "Ошибка в формате периода"  # Возвращаем осмысленный текст, если не смогли обработать

> Юлия Мамедова:
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

> Юлия Мамедова:
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

> Юлия Мамедова:
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
        # Проверяем если период строка типа "фев.25"
        if period_str.startswith(month_abbr):
            year_part = period_str[len(month_abbr):]  # Получаем оставшуюся часть строки
            year_part = year_part.replace('.', '')  # Убираем точку

            # Проверяем, если год состоит из двух цифр
            if len(year_part) == 2 and year_part.isdigit():
                year = 2000 + int(year_part)  # Преобразуем в 4-значный год (например, "25" -> 2025)
            elif len(year_part) == 4 and year_part.isdigit():  # Если год уже 4 цифры
                year = int(year_part)
            else:
                return "Ошибка в формате периода"  # Если год некорректный

            # Получаем последний день месяца
            last_day = calendar.monthrange(year, month_num)[1]
            return f"01.{month_num:02}.{year}-{last_day}.{month_num:02}.{year}"

    return "Ошибка в формате периода"  # Если формат не распознан

> Юлия Мамедова:
Опасно

> Юлия Мамедова:
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
        return df.iloc[row_idx:, col_idx:]
    return None

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))
    df = df[sheet_name]
    
    # Поиск проекта и периода
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    period_raw = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")
    
    period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower() and "отсутствует" not in period_raw.lower():
        period = parse_period(period_raw)
    
    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)
    
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

> Юлия Мамедова:
st.success(f"Период: {period}" if "не найден" not in period.lower() else period)

> Юлия Мамедова:
# Добавлена дополнительная проверка для обработки значений, подобных "сезонный коэффициент"
st.success(f"Период: {period}" if isinstance(period, str) and "не найден" not in period.lower() and "сезонныйкоэффициент" not in period.lower() else "Некорректный период")

> Юлия Мамедова:
def parse_period(period_str):
    """
    Преобразует период, заданный в сокращенном формате.
    Если период содержит "-", считаем, что это уже диапазон дат и возвращаем его как есть.
    Если период вида "фев.25" или "фев.2025", то он преобразуется в формат:
    "01.MM.YYYY-last_day.MM.YYYY", где last_day – последний день месяца.
    """
    if not isinstance(period_str, str):
        return period_str
    
    # Если встречаем слово "сезонный коэффициент", это не период, и возвращаем специальное сообщение
    if "сезонный коэффициент" in period_str.lower():
        return "Сезонный коэффициент, не период"

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

> Юлия Мамедова:
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
                year = int("20" + year_part)  # если год в формате 2 цифр (например, 25 -> 2025)
            elif len(year_part) == 4:
                year = int(year_part)  # если год в формате 4 цифр
            else:
                return period_str  # если год задан некорректно, возвращаем исходное значение

            last_day = calendar.monthrange(year, month)[1]  # получаем последний день месяца
            return f"01.{month:02}.{year}-{last_day}.{month:02}.{year}"  # возвращаем период в формате "01.MM.YYYY-last_day.MM.YYYY"
    
    return period_str  # если ничего не найдено, возвращаем исходное значение

> Юлия Мамедова:
Давай сделаем так. Если месяц фев. То это февраль и так далее

> Юлия Мамедова:
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
                year = int("20" + year_part)  # если год в формате 2 цифр (например, 25 -> 2025)
            elif len(year_part) == 4:
                year = int(year_part)  # если год в формате 4 цифр
            else:
                return period_str  # если год задан некорректно, возвращаем исходное значение

            # Проверяем, какой последний день месяца
            last_day = calendar.monthrange(year, month)[1]
            return f"01.{month:02}.{year}-{last_day}.{month:02}.{year}"  # возвращаем период в формате "01.MM.YYYY-last_day.MM.YYYY"
    
    return period_str  # если ничего не найдено, возвращаем исходное значение

> Юлия Мамедова:
period = period_raw
    if isinstance(period_raw, str) and "не найден" not in period_raw.lower():
        period = parse_period(period_raw)

> Юлия Мамедова:
# Проверка на наличие фразы "не найден" и последующее преобразование периода
period = period_raw
if isinstance(period_raw, str) and "не найден" not in period_raw.lower() and "сезонныйкоэффициент" not in period_raw.lower():
    period = parse_period(period_raw)

> Юлия Мамедова:
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
                year = int("20" + year_part)  # если год в формате 2 цифр (например, 25 -> 2025)
            elif len(year_part) == 4:
                year = int(year_part)  # если год в формате 4 цифр
            else:
                return period_str  # если год задан некорректно, возвращаем исходное значение

            # Проверяем, какой последний день месяца
            last_day = calendar.monthrange(year, month)[1]
            return f"01.{month:02}.{year}-{last_day}.{month:02}.{year}"  # возвращаем период в формате "01.MM.YYYY-last_day.MM.YYYY"
    
    return period_str  # если ничего не найдено, возвращаем исходное значение

> Юлия Мамедова:
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

# Применение в основной логике
period = period_raw
if isinstance(period_raw, str) and "не найден" not in period_raw.lower():
    # Перекидываем в переменную period как строку и преобразуем если нужно
    period = parse_period(period_raw)

> Юлия Мамедова:
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

> Юлия Мамедова:
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
                        return df.iloc[idx+1:]  # Возвращаем строки после найденного месяца
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

> Юлия Мамедова:
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

> Юлия Мамедова:
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
        return df.iloc[row_idx:, col_idx:]
    return None

> Юлия Мамедова:
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

> Юлия Мамедова:
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

> Юлия Мамедова:
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
