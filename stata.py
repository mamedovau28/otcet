import pandas as pd
import streamlit as st

def find_project_name(df):
    for col_idx, col in enumerate(df.columns):  # Перебираем все колонки
        for idx, value in df[col].items():  # Перебираем строки в колонке
            if isinstance(value, str) and "проект" in value.lower():  # Ищем слово "проект"
                next_col_idx = col_idx + 1  # Индекс следующего столбца
                if next_col_idx < len(df.columns):  # Проверяем, есть ли следующий столбец
                    next_col = df.columns[next_col_idx]  # Получаем название следующего столбца
                    return df[next_col][idx]  # Возвращаем значение из следующего столбца
                else:
                    return "Название проекта отсутствует"  # Если следующего столбца нет
    return "Проект не найден"  # Если строка с "проект" не найдена

st.title("Загрузка и обработка данных")

uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)  # Загружаем все листы
    sheet_name = st.selectbox("Выберите лист", list(df.keys()))  # Выбираем лист
    df = df[sheet_name]  # Берем данные выбранного листа
    
    project_name = find_project_name(df)
    
    if project_name == "Проект не найден" or project_name == "Название проекта отсутствует":
        st.warning(project_name)
    else:
        st.success(f"Название проекта найдено: {project_name}")

    st.dataframe(df)  # Показываем загруженную таблицу
