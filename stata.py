import streamlit as st
import pandas as pd

COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"],
    "охват": ["охват", "reach"]
}

PLATFORM_MAPPING = {
    "площадка": ["площадка", "название сайта", "сайт", "ресурс"]
}

def standardize_columns(df, mapping):
    df.columns = df.columns.astype(str).str.lower().str.strip()
    column_map = {}
    for standard_col, possible_names in mapping.items():
        for col in df.columns:
            if any(word in col for word in possible_names):
                column_map[standard_col] = col
                break
    return df.rename(columns=column_map), column_map

def clean_mp(mp_df):
    for i, row in mp_df.iterrows():
        if row.astype(str).str.contains("площадка", case=False, na=False).any() or \
           row.astype(str).str.contains("название сайта", case=False, na=False).any() or \
           row.astype(str).str.contains("ресурс", case=False, na=False).any():
            mp_df = mp_df.iloc[i:].reset_index(drop=True)
            mp_df.columns = mp_df.iloc[0]
            mp_df = mp_df[1:].reset_index(drop=True)
            return mp_df
    return None

def process_mp(mp_df):
    mp_df = clean_mp(mp_df)
    if mp_df is None:
        st.error("Не удалось найти строку с заголовками, содержащую 'площадка', 'название сайта' или 'ресурс'.")
        return None, {}
    
    mp_df, col_map = standardize_columns(mp_df, PLATFORM_MAPPING)
    
    required_cols = {"площадка", "показы", "клики"}
    missing_columns = [col for col in required_cols if col not in col_map]
    if missing_columns:
        st.error(f"Отсутствуют обязательные столбцы: {', '.join(missing_columns)}")
        return None, col_map

    selected_cols = list(required_cols)
    if "охват" in col_map:
        selected_cols.append("охват")
    mp_df = mp_df[[col_map[col] for col in selected_cols if col in col_map]]
    
    mp_df.dropna(subset=[col_map["площадка"], col_map["показы"], col_map["клики"]], how="any", inplace=True)

    try:
        mp_df[col_map["показы"]] = pd.to_numeric(mp_df[col_map["показы"]], errors='coerce')
        mp_df = mp_df[mp_df[col_map["показы"]] != 0]
    except Exception as e:
        st.warning("Не удалось привести столбец 'показы' к числовому типу. Строки не фильтруются по этому столбцу.")
    
    st.write("Обработанный медиаплан:")
    st.dataframe(mp_df)
    return mp_df, col_map

def process_data(df):
    df, col_map = standardize_columns(df, COLUMN_MAPPING)
    df.fillna(0, inplace=True)
    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")
    for key in ["показы", "клики", "охват", "расход"]:
        if key in col_map and not pd.api.types.is_numeric_dtype(df[col_map[key]]):
            df[col_map[key]] = df[col_map[key]].astype(str).str.replace(r"[^\d]", "", regex=True)
            df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)
    if "расход" in col_map:
        df[col_map["расход"]] = df[col_map["расход"]] / 100
    if "охват" in col_map and "показы" in col_map:
        def adjust_coverage(row):
            coverage = row[col_map["охват"]]
            impressions = row[col_map["показы"]]
            if coverage > 0 and impressions > 0:
                if impressions / coverage > 10:
                    return impressions * coverage / 100
            return round(coverage)
        df["охват"] = df.apply(adjust_coverage, axis=1)
    if "расход" in col_map:
        df["расход с ндс"] = df[col_map["расход"]] * 1.2
    if "клики" in col_map and "показы" in col_map:
        df["ctr"] = df.apply(lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] > 0 else 0, axis=1)
    return df, col_map

# Интерфейс Streamlit
st.title("Анализ рекламных кампаний")
st.header("Загрузите медиаплан (МП) (только Excel)")

mp_file = st.file_uploader("Выберите файл с медиапланом (Excel)", type=["xlsx"], key="mp_uploader")

mp_df = None
if mp_file:
    xls = pd.ExcelFile(mp_file)
    sheet_names = xls.sheet_names
    if len(sheet_names) > 1:
        sheet_name = st.selectbox("Выберите лист с медиапланом", sheet_names, key="mp_sheet_select")
    else:
        sheet_name = sheet_names[0]
    mp_df = pd.read_excel(mp_file, sheet_name=sheet_name)
    st.write("Медиаплан загружен:", sheet_name)
    try:
        mp_df, mp_col_map = process_mp(mp_df)
    except Exception as e:
        st.error(f"Ошибка обработки МП: {e}")
    if mp_df is not None and "площадка" in mp_col_map:
        platforms = mp_df[mp_col_map["площадка"]].dropna().unique()
        st.subheader("Найденные рекламные площадки:")
        st.write(platforms)
    else:
        st.error("Не найден столбец с рекламными площадками.")
