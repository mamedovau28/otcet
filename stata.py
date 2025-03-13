import pandas as pd
import streamlit as st

def find_value_by_keyword(df, keyword, not_found_msg, empty_msg):
    """Функция ищет строку с нужным словом и берет значение из следующего столбца"""
    for col_idx, col in enumerate(df.columns):  # Перебираем все колонки
        for idx, value in df[col].items():  # Перебираем строки в колонке
            if isinstance(value, str) and keyword in value.lower():  # Ищем слово
                next_col_idx = col_idx + 1  # Индекс следующего столбца
                if next_col_idx < len(df.columns):  # Проверяем, есть ли следующий столбец
                    next_col = df.columns[next_col_idx]  # Получаем название следующего столбца
                    return df[next_col][idx]  # Возвращаем значение из следующего столбца
                else:
                    return empty_msg  # Если следующего столбца нет
    return not_found_msg  # Если строка с нужным словом не найдена

st.title("Загрузка и обработка данных")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)  # Загружаем все листы
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))  # Выбираем лист
    df = df[sheet_name]  # Берем данные выбранного листа
    
    # Поиск названия проекта
    project_name = find_value_by_keyword(df, "проект", "Проект не найден", "Название проекта отсутствует")
    # Поиск периода
    period = find_value_by_keyword(df, "период", "Период не найден", "Период отсутствует")
    
    # Вывод результатов
    if project_name.startswith("Проект не найден") or project_name.startswith("Название проекта отсутствует"):
        st.warning(project_name)
    else:
        st.success(f"Название проекта найдено: {project_name}")

    if period.startswith("Период не найден") or period.startswith("Период отсутствует"):
        st.warning(period)
    else:
        st.success(f"Период найден: {period}")

    st.dataframe(df)  # Показываем загруженную таблицу
