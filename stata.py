import pandas as pd
import streamlit as st

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

def find_table_start(df):
    """Находит координаты ячейки с '№' и возвращает индекс строки и колонки"""
    for col_idx, col in enumerate(df.columns):
        for row_idx, value in df[col].items():
            if isinstance(value, str) and "№" in value:
                return row_idx, col_idx  # Возвращаем строку и колонку, где нашли "№"
    return None, None  

def extract_campaigns_table(df):
    """Извлекает таблицу с рекламными кампаниями, начиная с найденной строки и колонки"""
    row_idx, col_idx = find_table_start(df)
    if row_idx is not None and col_idx is not None:
        # Извлекаем таблицу
        table_data = df.iloc[row_idx:, col_idx:]
        
        # Удаляем строки, где в 2 из первых 3 столбцов отсутствуют данные
        table_data = table_data.dropna(subset=table_data.columns[:5], thresh=3)
        
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
