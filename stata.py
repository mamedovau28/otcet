import streamlit as st
import pandas as pd

# Функция для загрузки Excel-файла
def load_excel(file):
    return pd.ExcelFile(file)

# Функция для загрузки Google Sheets
def load_google_sheets(sheet_url):
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)  # Открываем первый лист
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

st.title("Загрузка данных с маркетплейса")

# Выбор способа загрузки данных
option = st.radio("Выберите источник данных:", ["Загрузить Excel", "Ссылка на Google Таблицу"])

df = None

if option == "Загрузить Excel":
    uploaded_file = st.file_uploader("Загрузите файл Excel", type=["xlsx", "xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file, sheet_name=None)  # Читаем все листы
        st.success("Файл загружен")
elif option == "Ссылка на Google Таблицу":
    sheet_url = st.text_input("Введите ссылку на Google Таблицу")
    if sheet_url:
        try:
            df = load_google_sheets(sheet_url)
            st.success("Google Таблица загружена")
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")

# Отображение загруженных данных
if df is not None:
    if isinstance(df, dict):  # Если загружены несколько листов из Excel
        sheet_name = st.selectbox("Выберите лист", list(df.keys()))
        st.dataframe(df[sheet_name])
    else:
        st.dataframe(df)
