import pandas as pd
import streamlit as st

def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Ищет строку с нужным словом и берет значение в зависимости от ситуации:
       - Если найден 'проект', то берем значение из следующего столбца.
       - Если найден 'ресурс', то берем значение из строки ниже в этом же столбце.
    """
    for col_idx, col in enumerate(df.columns):  
        for idx, value in df[col].items():  
            if isinstance(value, str) and keyword in value.lower():  
                if "ресурс" in value.lower():  
                    next_row_idx = idx + 1  
                    if next_row_idx < len(df):  
                        return df[col][next_row_idx]  
                    else:
                        return empty_msg  
                else:  # По умолчанию считаем, что это "проект"
                    next_col_idx = col_idx + 1  
                    if next_col_idx < len(df.columns):  
                        next_col = df.columns[next_col_idx]  
                        return df[next_col][idx]  
                    else:
                        return empty_msg  
    return not_found_msg  

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
        table_data = df.iloc[row_idx:, col_idx:]
        
        # Если есть столбец "месяц", удаляем пустые строки в нем
        if "месяц" in table_data.columns.str.lower():
            table_data = table_data.dropna(subset=["месяц"])

        return table_data
    return None  

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)  
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))  
    df = df[sheet_name]  
    
    # Поиск проекта, ресурса и периода
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    resource_name = find_value_by_keyword(df, "ресурс", "Ресурс не найден", "Название ресурса отсутствует")
    period = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")

    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)

    if resource_name and (resource_name.startswith("Ресурс не найден") or resource_name.startswith("Название ресурса отсутствует")):
        st.warning(resource_name)
    else:
        st.success(f"Название ресурса: {resource_name}")

    # Вывод проекта, ресурса и периода
    st.subheader("Информация о проекте")
    if project_name.startswith("Проект не найден") or project_name.startswith("Название проекта отсутствует"):
        st.warning(project_name)
    else:
        st.success(f"Название проекта: {project_name}")

    if resource_name.startswith("Ресурс не найден") or resource_name.startswith("Название ресурса отсутствует"):
        st.warning(resource_name)
    else:
        st.success(f"Название ресурса: {resource_name}")

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
