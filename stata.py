import streamlit as st
import pandas as pd  

st.title("Отчет по статистике РК")  

# Выбор способа загрузки данных  
option = st.radio("Загрузите МП:", ["Загрузить Excel", "Ссылка на Google Таблицу"])  

df = None  

if option == "Загрузить Excel":  
    uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])  
    if uploaded_file:  
        df = pd.read_excel(uploaded_file)  
        st.success("Файл загружен")  

elif option == "Ссылка на Google Таблицу":  
    sheet_url = st.text_input("Введите ссылку на Google Таблицу (формат CSV)")  
    if sheet_url:  
        try:  
            csv_url = sheet_url.replace("/edit#", "/export?format=csv")  # Преобразуем ссылку  
            df = pd.read_csv(csv_url)  
            st.success("Google Таблица загружена")  
        except Exception as e:  
            st.error(f"Ошибка загрузки: {e}")  

# Отображение загруженных данных  
if df is not None:  
    st.dataframe(df)
