import pandas as pd
import streamlit as st

def find_value_in_first_column(df, keyword, not_found_msg):
    """Ищет строку с нужным словом в первом столбце и берет значение из следующего столбца"""
    for idx, value in df.iloc[:, 0].items():  # Проходим по первому столбцу
        if isinstance(value, str) and keyword in value.lower():
            # Берем значение из следующего столбца
            next_col_value = df.iloc[idx, 1] if idx + 1 < len(df.columns) else None
            return next_col_value if next_col_value else not_found_msg
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
        
        # Удаляем строки, где в 3 из первых 5 столбцов отсутствуют данные
        table_data = table_data.dropna(subset=table_data.columns[:5], thresh=3)
        
        return table_data
    return None  

st.title("Обработка данных рекламных кампаний")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    # Чтение файла
    df = pd.read_excel(uploaded_file, sheet_name=None)  
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))  
    df = df[sheet_name]  

    # Удаляем пустые строки из первого столбца
    df = df[df.iloc[:, 0].notna()]

    # Поиск проекта и периода в первом столбце
    project_name = find_value_in_first_column(df, "проект", "Проект не найден")
    period = find_value_in_first_column(df, "период", "Период не найден")

    # Поиск таблицы с рекламными кампаниями
    campaigns_table = extract_campaigns_table(df)

    # Вывод проекта и периода
    st.subheader("Информация о проекте")
    if project_name == "Проект не найден":
        st.warning(project_name)
    else:
        st.success(f"Название проекта: {project_name}")

    if period == "Период не найден":
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
