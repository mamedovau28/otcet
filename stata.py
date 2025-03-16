import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pandas.tseries.offsets import MonthEnd

# Словарь для сопоставления названий колонок в отчетах
COLUMN_MAPPING = {
    "дата": ["дата", "date"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "расход": ["расход", "затраты", "cost", "спенд", "расход до ндс", "расходдондс"],
    "охват": ["охват", "reach"]
}

# Словарь для сопоставления названий колонок в МП (рекламные площадки)
PLATFORM_MAPPING = {
    "площадка": ["площадка", "название сайта", "ресурс"]
}

report_col_map = {
    "площадка": ["площадка", "название сайта", "ресурс"],
    "показы": ["показы", "импрессии", "impressions"],
    "клики": ["клики", "clicks"],
    "охват": ["охват", "reach"],
    "бюджет": [r".*ндс и.*"]
}

def standardize_columns(df, mapping):
    """
    Приводит названия колонок к стандартному виду по переданному mapping.
    Все имена столбцов приводятся к нижнему регистру и обрезаются пробелы.
    Столбцы с заголовком 'nan' удаляются.
    """
    df.columns = df.columns.astype(str).str.lower().str.strip()
    # Удаляем столбцы с заголовком 'nan'
    df = df.loc[:, df.columns != 'nan']
    
    column_map = {}
    for standard_col, possible_names in mapping.items():
        for col in df.columns:
            if any(word in col for word in possible_names):
                column_map[standard_col] = col
                break
                
    return df.rename(columns=column_map), column_map

def filter_columns(df, is_mp=False):
    """
    Оставляет только нужные столбцы в определенном порядке.
    Фильтрация применяется только к файлам медиаплана (если is_mp=True).
    - дата (если есть)
    - площадка (если есть)
    - показы (если есть)
    - клики (если есть)
    - охват (если есть)
    - расход (если есть)
    - столбец, содержащий "с учетом НДС и АК" (если есть)
    """
    # Если это медиаплан, применяем фильтрацию
    if is_mp:
        required_columns = []

        # Заменяем все символы "-" и значения NaN и None на 0
        df.replace({"-": 0}, inplace=True)  # Заменяем "-" на 0
        df.fillna(0, inplace=True)  # Заменяем NaN и None на 0

        for col in df.columns:
            col_lower = col.lower().strip()

            if "дата" in col_lower:
                required_columns.append(col)
            elif any(keyword in col_lower for keyword in ["площадка", "название сайта", "ресурс"]):
                required_columns.append(col)
            elif "показ" in col_lower:
                required_columns.append(col)
            elif "клик" in col_lower:
                required_columns.append(col)
            elif "охват" in col_lower:
                required_columns.append(col)
            elif "расход" in col_lower:
                required_columns.append(col)
            elif re.search(r".* ндс и .*", col_lower):
                required_columns.append(col)
                
        # Возвращаем DataFrame с колонками в нужном порядке
        return df[required_columns] if required_columns else df
        
        # Удаляем строки, где значение в столбце "показы" равно 0
        if "показы" in df.columns:
            df = df[df["показы"] != 0]

        return df

    # Если это не медиаплан (например, отчет), возвращаем df без изменений
    return df

def process_data(df):
    """
    Обрабатывает загруженные данные (Excel или Google-таблицы):
      - Стандартизирует имена колонок
      - Преобразует дату, приводит числовые значения к нужному типу
      - Рассчитывает расход с НДС и CTR
      - Очищает ненужные столбцы
    """
    df, col_map = standardize_columns(df, COLUMN_MAPPING)
    df.fillna(0, inplace=True)

    # Преобразуем дату в формат datetime
    if "дата" in col_map:
        df[col_map["дата"]] = pd.to_datetime(df[col_map["дата"]], format="%d.%m.%Y", errors="coerce")

    # Приведение к числовому типу (исключаем повторное умножение)
    for key in ["показы", "клики", "охват", "расход"]:
        if key in col_map:
            if not pd.api.types.is_numeric_dtype(df[col_map[key]]):  # Только если не число
                df[col_map[key]] = df[col_map[key]].astype(str).str.replace(r"[^\d,]", "", regex=True)
                df[col_map[key]] = df[col_map[key]].str.replace(",", ".")  
                df[col_map[key]] = pd.to_numeric(df[col_map[key]], errors='coerce').fillna(0)

    # Корректировка охвата
    if "охват" in col_map and "показы" in col_map:
        def adjust_coverage(row):
            coverage = row[col_map["охват"]]
            impressions = row[col_map["показы"]]

            # Убеждаемся, что coverage — это число
            if isinstance(coverage, str):
                coverage = coverage.replace(",", ".")
                coverage = pd.to_numeric(coverage, errors="coerce")

            if pd.isna(coverage) or coverage == 0:
                return 0  

            # Проверяем, является ли coverage долей (например, 0.2) и содержатся ли нули после запятой
            if 0 < coverage < 1:  # Проверяем, что число меньше 1 (например, 0.2)
                str_coverage = str(coverage)
                # Если число имеет два нуля после запятой (например, 0.002), считаем это процентом
                if len(str_coverage.split('.')[1]) > 2:
                    coverage *= 100  # Умножаем на 100, если это процент

            # Коррекция данных (если покрытие не должно быть в 10 раз меньше показов)
            if coverage > 0 and impressions > 0 and impressions / coverage > 10:
                return impressions * coverage

            return round(coverage)

        df["охват"] = df.apply(adjust_coverage, axis=1)

    # Расчет расхода с НДС
    if "расход" in col_map and "расход с ндс" not in df.columns:
        df["расход с ндс"] = df[col_map["расход"]] * 1.2

    # Расчет CTR
    if "клики" in col_map and "показы" in col_map and "ctr" not in df.columns:
        df["ctr"] = df.apply(
            lambda row: row[col_map["клики"]] / row[col_map["показы"]] if row[col_map["показы"]] > 0 else 0,
            axis=1
        )

    # Фильтрация нужных столбцов
    df = filter_columns(df)

    return df, col_map

    
def clean_mp(mp_df):
    """
    Ищет первую строку, содержащую слово "площадка", "название сайта" или "ресурс" (без учета регистра).
    Считает эту строку заголовочной и возвращает таблицу, начиная с этой строки.
    """
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
    """
    Обрабатывает медиаплан (МП):
      - Вызывает clean_mp, чтобы найти строку с заголовками (начало таблицы).
      - Стандартизирует имена колонок по PLATFORM_MAPPING.
      - Возвращает очищенную таблицу и mapping найденных столбцов.
    """
    mp_df = clean_mp(mp_df)
    if mp_df is None:
        st.error("Ошибка: не удалось найти строку с заголовками, содержащую 'площадка', 'название сайта' или 'ресурс'.")
        return None, {}

    mp_df, col_map = standardize_columns(mp_df, PLATFORM_MAPPING)

    # Применяем фильтрацию столбцов сразу после стандартизации
    mp_df = filter_columns(mp_df, is_mp=True)

    return mp_df, col_map

def find_column(df, keywords):
    """
    Функция для поиска столбцов, содержащих ключевые слова.
    """
    found_columns = {}
    for keyword in keywords:
        column_matches = [col for col in df.columns if re.search(keyword, col, re.IGNORECASE)]
        if column_matches:
            found_columns[keyword] = column_matches[0]  # Сохраняем первый найденный столбец
    return found_columns

def calculate_campaign_period(df):
    """
    Определяем дату начала и конца рекламной кампании.
    """
    # Ищем столбцы "дата" и "показ" независимо от регистра
    date_col = next((col for col in df.columns if "дата" in col.lower()), None)
    impressions_col = next((col for col in df.columns if "показ" in col.lower()), None)

    if not date_col or not impressions_col:
        st.error("Не найдены столбцы 'дата' или 'показы'.")
        return None, None

    # Преобразуем столбец с датами в формат datetime
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')  # Если ошибка, заменяется на NaT

    # Фильтруем только те строки, где показы больше 10
    df_filtered = df[df[impressions_col] > 10]

    if df_filtered.empty:
        st.error("Нет данных о показах больше 10.")
        return None, None

    # Определяем минимальную и максимальную дату
    start_date = df_filtered[date_col].min()
    # Определяем последнюю дату с показами
    last_impression_date = df_filtered[date_col].max()
    # Определяем конец месяца для этой даты
    end_date = last_impression_date + MonthEnd(0)  # Переносим на конец месяца

    # Рассчитываем количество дней между началом и концом кампании
    campaign_days = (end_date - start_date).days + 1  # +1, чтобы включить оба дня

    st.write(f"Количество рекламных дней: {campaign_days}")

    return start_date, end_date
    
# Основная функция для проверки совпадений
def check_matching_campaign(mp_df, df, campaign_name):
    # Проверка на наличие данных в mp_df и отчете
    if mp_df is None or df is None:
        return "Медиаплан или отчет не загружены. Проверьте загрузку данных.", None

    # Приводим название РК к нижнему регистру
    campaign_name = campaign_name.strip().lower()

    # Список возможных имен столбцов для площадки
    possible_columns = ['площадка', 'название сайта', 'ресурс']
    
    # Ищем столбец, который может содержать название площадки
    match_column = None
    for col in possible_columns:
        if col in mp_df.columns:
            match_column = col
            break  # Прерываем, как только нашли подходящий столбец

    if match_column is None:
        return "Не найден столбец с названием площадки в медиаплане.", None

    # Приводим название площадки к нижнему регистру
    mp_df['площадка_lower'] = mp_df[match_column].str.strip().str.lower()

    # Поиск совпадений по названию РК
    matching_rows = mp_df[mp_df['площадка_lower'].str.contains(campaign_name, na=False)]

    if not matching_rows.empty:
        # Если найдено совпадение
        matched_campaign = matching_rows[match_column].iloc[0]
        match_message = f"Найдено совпадение по площадке: {matched_campaign}"

        # Сохраняем найденные строки как отдельную таблицу (DataFrame)
        saved_matching_rows = matching_rows.copy()
        saved_matching_rows['площадка_lower'] = saved_matching_rows[match_column].str.strip().str.lower()

        # Проверяем наличие столбцов для показов, кликов, охвата и бюджета с НДС
        required_columns = {
            "показы": r"\bпоказы?\b",
            "клики": r"\bклики?\b",
            "охват": r"\bохват\b",
            "бюджет с ндс": r"\b(ндс\s*и)\b"
        }
        
        found_columns = {}
        for col, regex in required_columns.items():
            matching_columns = [column for column in mp_df.columns if re.search(regex, column, re.IGNORECASE)]
            if matching_columns:
                found_columns[col] = matching_columns
        
        # Выводим обновленную таблицу
        st.write("Обновленная таблица с расчетами:")
        st.write(saved_matching_rows)

        # Сохраняем обновленную таблицу в файл
        saved_matching_rows.to_csv("updated_campaign_data.csv", index=False)
        
        return match_message, saved_matching_rows
    else:
        return "Совпадений по площадке не найдено.", None


def transfer_numeric_data(df, saved_matching_rows, campaign_days, start_date):
    """
    Переносим числовые данные из saved_matching_rows в df, начиная с start_date,
    разделяя значения на campaign_days. До start_date оставляем 0.
    Присваиваем столбцам новые имена в зависимости от их содержимого.
    Добавляем расчет разницы и процентного отклонения между фактическими и плановыми показателями.
    """
    if saved_matching_rows is None or df is None or campaign_days <= 0 or start_date is None:
        return df  # Если нет данных или некорректное число дней, возвращаем df без изменений

    # Находим все числовые столбцы в saved_matching_rows
    numeric_cols = saved_matching_rows.select_dtypes(include=['number']).columns

    if numeric_cols.empty:
        print("Нет числовых столбцов для переноса.")
        return df

    # Определяем столбец с датами в df (если он есть)
    date_col = None
    for col in df.columns:
        if "дата" in col.lower():
            date_col = col
            break

    if date_col is None:
        print("Не найден столбец с датой в df.")
        return df

    # Преобразуем столбец даты в формат datetime
    df[date_col] = pd.to_datetime(df[date_col])

    # Маска для строк, где дата меньше start_date
    before_start_mask = df[date_col] < start_date

    # Словарь для хранения соответствия плановых и фактических показателей
    plan_cols = {
        "показы план": "показы",
        "клики план": "клики",
        "охват план": "охват",
        "бюджет план": "расход с ндс"
    }

    # Для каждого числового столбца находим, как его назвать, и дублируем данные
    for col in numeric_cols:
        # Делим значения на campaign_days
        df[col] = saved_matching_rows[col].iloc[0] / campaign_days
        
        # Применяем маску для строк до start_date, где значения будут равны 0
        df.loc[before_start_mask, col] = 0

        # Переименовываем столбцы в зависимости от их содержания
        if "ндс" in col.lower():
            df.rename(columns={col: "бюджет план"}, inplace=True)
        elif "показы" in col.lower() and "план" in col.lower():
            df.rename(columns={col: "показы план"}, inplace=True)
        elif "клики" in col.lower() and "план" in col.lower():
            df.rename(columns={col: "клики план"}, inplace=True)
        elif "охват" in col.lower():
            df.rename(columns={col: "охват план"}, inplace=True)
        # Можно добавить дополнительные условия по другим столбцам, если нужно

    return df

def check_for_differences(df_filtered, existing_cols, plan_cols):
    warnings = []
    differences = []  # Список для хранения расхождений в суммах
    
    # Проверка на наличие столбцов
    for plan_col, fact_col in zip(plan_cols, existing_cols):
        if plan_col in df_filtered.columns and fact_col in df_filtered.columns:
            
            # Фильтруем строки, где показы больше 0
            df_filtered_valid = df_filtered[df_filtered[fact_col] > 10]

            # Суммируем значения только там, где показы больше 0
            fact_total = df_filtered_valid[fact_col].sum()
            plan_total = df_filtered_valid[plan_col].sum()

            if plan_total > 0:
                diff = fact_total - plan_total
                diff_percent = (diff / plan_total) * 100

                # Добавляем информацию о расхождении в таблицу
                differences.append({
                    'Столбец факта': fact_col,
                    'Столбец плана': plan_col,
                    'Фактическое значение': fact_total,
                    'Плановое значение': plan_total,
                    'Разница': diff,
                    'Процентное расхождение': f"{diff_percent:+.2f}%" if abs(diff_percent) > 1 else "0.00%"
                })

                if abs(diff_percent) > 1:
                    warnings.append(f"⚠️ Разница по {fact_col}: {diff:+,.0f} ({diff_percent:+.2f}%)")
                else:
                    warnings.append(f"✅ Нет значительных расхождений по {fact_col}.")
            else:
                # Если плановое значение равно нулю, считаем, что расхождения нет
                differences.append({
                    'Столбец факта': fact_col,
                    'Столбец плана': plan_col,
                    'Фактическое значение': fact_total,
                    'Плановое значение': plan_total,
                    'Разница': 0,
                    'Процентное расхождение': "0.00%"
                })
                warnings.append(f"✅ Нет данных по {fact_col} для расхождения.")
    
    # Создаем итоговую таблицу только после завершения обработки всех столбцов
    if differences:
        diff_df = pd.DataFrame(differences)
        st.write("Таблица расхождений:")
        st.dataframe(diff_df)  # Отображаем итоговую таблицу расхождений
    
    return warnings


    
st.title("Анализ рекламных кампаний")

# === Загрузка медиаплана ===
st.header("Загрузите медиаплан")
mp_file = st.file_uploader("Выберите файл с медиапланом", type=["xlsx"], key="mp_uploader")

mp_df = None
if mp_file:
    # Чтение Excel файла
    xls = pd.ExcelFile(mp_file)
    sheet_names = xls.sheet_names
    if len(sheet_names) > 1:
        sheet_name = st.selectbox("Выберите лист с медиапланом", sheet_names, key="mp_sheet_select")
    else:
        sheet_name = sheet_names[0]
    
    # Загрузка данных с выбранного листа
    mp_df = pd.read_excel(mp_file, sheet_name=sheet_name)
    st.write("Медиаплан загружен:", sheet_name)

    # Обработка медиаплана, включая фильтрацию столбцов
    mp_df, mp_col_map = process_mp(mp_df)  # Фильтрация теперь будет применяться здесь

    if mp_df is not None:
        st.subheader("Обработанный медиаплан")

        # Убираем дубликаты столбцов
        mp_df = mp_df.loc[:, ~mp_df.columns.duplicated()].copy()

        # Фильтрация столбцов с нужным порядком и удаление строк с нулевыми показами
        mp_df = filter_columns(mp_df, is_mp=True)  # Применяем фильтрацию для медиаплана

        # Находим столбец, который содержит "показы" в своем названии
        show_column = [col for col in mp_df.columns if "показы" in col.lower()]

        if show_column:
            # Преобразуем столбец в числовой тип
            mp_df[show_column[0]] = pd.to_numeric(mp_df[show_column[0]], errors="coerce")  # Преобразуем в числовой тип, NaN для ошибок

            # Удаляем строки, где показы = 0 или NaN
            mp_df = mp_df[mp_df[show_column[0]] > 0]  # Оставляем только строки с показами больше 0

        # Ищем столбец, который содержит "НДС"
        ndc_column = [col for col in mp_df.columns if "ндс" in col.lower()]

        # Если такой столбец найден, приводим его к числовому типу и удаляем строки с нулями
        if ndc_column:
            ndc_column_name = ndc_column[0]  # Получаем имя столбца
            mp_df[ndc_column_name] = pd.to_numeric(mp_df[ndc_column_name], errors="coerce")  # Преобразуем в числовой тип, NaN для ошибок
            # Удаляем строки, где значение в столбце НДС = 0 или NaN
            mp_df = mp_df[mp_df[ndc_column_name] > 0]  # Оставляем только строки с показателями больше 0

        # Оставляем только те столбцы, где количество ненулевых значений больше 1
        mp_df = mp_df.loc[:, (mp_df != 0).sum(axis=0) > 1]

        # Отображаем обработанный медиаплан
        st.dataframe(mp_df)

# === Загрузка отчетов ===
# Заголовок страницы
st.header("Загрузите статистику РК")

# Применяем CSS для изменения фона и уменьшения ширины
st.markdown("""
    <style>
        .stNumberInput input {
            background-color: #f0f8e0;  /* светло-салатовый цвет */
            width: 50%;  /* Уменьшаем ширину в два раза */
        }
    </style>
""", unsafe_allow_html=True)

# Число загрузок, которое будет определять количество файлов
num_uploads = st.number_input("Выберите количество файлов для загрузки", min_value=1, max_value=20, value=1, key="num_uploads")

# Цикл для создания соответствующего числа загрузок
for i in range(1, num_uploads + 1):
    # Создание селектора для способа загрузки
    upload_option = st.selectbox(
        f"Способ загрузки статистики площадки {i}", 
        ["Не выбрано", "Загрузить Excel-файл", "Ссылка на Google-таблицу"], 
        key=f"upload_option_{i}"
    )

    df = None
    campaign_name = None

    if upload_option == "Загрузить Excel-файл":
        uploaded_file = st.file_uploader(f"Загрузите Excel-файл {i}", type=["xlsx"], key=f"file_uploader_{i}")
        if uploaded_file:
            xls = pd.ExcelFile(uploaded_file)  # Загружаем файл в объект ExcelFile
            sheet_names_otchet = xls.sheet_names  # Получаем список всех листов
            # Проверяем, есть ли несколько листов, и предлагаем выбрать нужный
            if len(sheet_names_otchet) > 1:
                selected_sheet = st.selectbox("Выберите лист со статистикой", sheet_names_otchet, key=f"sheet_names_otchet_{i}")
            else:
                selected_sheet = sheet_names_otchet[0]
            # Читаем данные с выбранного листа
            df = pd.read_excel(xls, sheet_name=selected_sheet)
            campaign_name = uploaded_file.name.split(".")[0]


    elif upload_option == "Ссылка на Google-таблицу":
        google_sheet_url = st.text_input(f"Ссылка на Google-таблицу {i}", key=f"google_sheet_url_{i}")
        if google_sheet_url:
            try:
                sheet_id = google_sheet_url.split("/d/")[1].split("/")[0]
                gid = google_sheet_url.split("gid=")[1].split("&")[0] if "gid=" in google_sheet_url else "0"
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
                df = pd.read_csv(csv_url)
                campaign_name = f"Загрузка {i}"
            except Exception as e:
                st.error(f"Ошибка при загрузке CSV: {e}")

    if df is not None:
        df, col_map = process_data(df)
        custom_campaign_name = st.text_input(
            f"Введите название РК {i} (или оставьте по умолчанию)", 
            value=campaign_name, 
            key=f"campaign_name_{i}"
        )
        st.write(f"Название РК: {custom_campaign_name}")

        # Проверка совпадений перед обработкой данных
        match_message, saved_matching_rows = check_matching_campaign(mp_df, df, custom_campaign_name)

        # Определяем период кампании
        start_date, end_date = calculate_campaign_period(df)
        if start_date and end_date:
            campaign_days = (end_date - start_date).days + 1

            if saved_matching_rows is not None:  # Если есть совпадения
                df = transfer_numeric_data(df, saved_matching_rows, campaign_days, start_date)  # Переносим данные в df
        
        # Вывод сообщений о совпадениях
        if isinstance(match_message, str):
            st.write(match_message)  
        else:
            st.write("Данные рекламной кампании:", match_message)  
            st.write("Обновленная таблица с расчетами:")
            st.write(saved_matching_rows)  

        if "дата" in col_map:
            min_date = df[col_map["дата"]].min().date()
            max_date = df[col_map["дата"]].max().date()

            # Исправлено: date_input возвращает список, его нужно распаковать
            start_date, end_date = st.date_input(
                "Выберите период", [min_date, max_date], key=f"date_input_{i}"
            )

            df_filtered = df[ 
                (df[col_map["дата"]].dt.date >= start_date) & 
                (df[col_map["дата"]].dt.date <= end_date)
            ]

            # Вычисления итогов
            needed_cols = ["показы", "клики", "охват", "расход с ндс"]
            existing_cols = [col for col in needed_cols if col in df_filtered.columns]
            summary = df_filtered[existing_cols].sum()

            total_impressions = summary.get("показы", 0)
            total_clicks = summary.get("клики", 0)
            ctr_value = total_clicks / total_impressions if total_impressions > 0 else 0
            total_reach = summary.get("охват", 0)
            total_spend_nds = summary.get("расход с ндс", 0)

            # Форматируем даты
            start_date_str = start_date.strftime("%d.%m.%Y")
            end_date_str = end_date.strftime("%d.%m.%Y")

            report_text = f"""
    {custom_campaign_name}
    Период: {start_date_str}-{end_date_str}
    Показы: {total_impressions:.0f}
    Клики: {total_clicks:.0f}
    CTR: {ctr_value:.2%}
    Охват: {total_reach:.0f}
    Расход с НДС: {format(total_spend_nds, ",.2f").replace(",", " ")} руб.
            """
            st.subheader(f"Итоговый отчёт {custom_campaign_name}")
            st.text_area(report_text, report_text, height=100)

            # Проверка расхождений и вывод предупреждений
            warnings = check_for_differences(df_filtered, existing_cols, ["показы план", "клики план", "охват план", "бюджет план"])
            if warnings:
                for warning in warnings:
                    st.warning(warning)

            # Исправлено: Приводим дату к строке для графиков
            df_filtered["дата_график"] = df_filtered[col_map["дата"]].dt.strftime('%d-%m')

            # График показов и охвата
            plt.figure(figsize=(10, 6))
            # Линия для фактических показов
            plt.plot(df_filtered["дата_график"], df_filtered["показы"], marker='o', label="Показы", color='b')
            # Линия для охвата
            plt.plot(df_filtered["дата_график"], df_filtered["охват"], marker='o', label="Охват", color='g')
            # Условие для добавления линии показов по плану, если такой столбец существует
            if "показы план" in df_filtered.columns:
                plt.plot(df_filtered["дата_график"], df_filtered["показы план"], linestyle='--', color='orange', linewidth=2, label="Показы по плану")
            # Заливка фона под линией охвата
            plt.fill_between(df_filtered["дата_график"], 0, df_filtered["охват"], color='g', alpha=0.2)
            # Заголовок и оформление графика
            plt.title(f"Показы и Охват по дням для {custom_campaign_name}")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.legend()
            # Отображаем график в Streamlit
            st.pyplot(plt)
            # Закрываем текущую фигуру, чтобы избежать лишних окон
            plt.close()

            # График кликов
            plt.figure(figsize=(10, 3))
            # Столбцы для фактических кликов
            plt.bar(df_filtered["дата_график"], df_filtered["клики"], color='r', alpha=0.7, label="Клики")
            # Условие для добавления столбцов кликов по плану, если такой столбец существует
            if "клики план" in df_filtered.columns:
                plt.bar(df_filtered["дата_график"], df_filtered["клики план"], color='orange', alpha=0.5, label="Клики по плану")
            plt.title(f"Клики по дням для {custom_campaign_name}")
            plt.xticks(rotation=45)
            plt.grid(True, axis='y')
            plt.legend()
            # Отображаем график в Streamlit
            st.pyplot(plt)
            # Закрываем текущую фигуру, чтобы избежать лишних окон
            plt.close()

    st.dataframe(df)
