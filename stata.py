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

