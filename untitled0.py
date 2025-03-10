
import subprocess
import streamlit as st
import pandas as pd
import numpy as np
import re

@st.cache_data
def load_excel_with_custom_header(file, identifier_value):
    """
    Загружает Excel-файл, ищет первую строку, в которой встречается identifier_value (в любой ячейке),
    и использует эту строку как заголовок.
    Если identifier_value не найден, возбуждает ошибку.
    """
    file.seek(0)  # сброс указателя файла
    df = pd.read_excel(file, header=None)
    
    header_index = None
    # Перебираем строки и ищем нужное значение во всех ячейках строки
    for i, row in df.iterrows():
        if row.astype(str).str.contains(identifier_value, case=False, na=False).any():
            header_index = i
            break
    if header_index is None:
        raise ValueError(f"Идентификатор '{identifier_value}' не найден в файле.")
    
    file.seek(0)
    df = pd.read_excel(file, header=header_index)
    return df

@st.cache_data
def load_excel_without_header(file):
    file.seek(0)
    return pd.read_excel(file, header=None)

def extract_report_period(file):
    """
    Извлекает отчетный период из первой строки файла с метками.
    Ожидается, что в ячейке A1 содержится строка вида:
    "Отчет за период с YYYY-MM-DD по YYYY-MM-DD" или "Отчет за период с DD.MM.YYYY по DD.MM.YYYY"
    """
    df = load_excel_without_header(file)
    header_str = str(df.iloc[0, 0])
    # Регулярное выражение для поиска дат
    match = re.search(r'Отчет за период с\s*([\d\.\-]+)\s*по\s*([\d\.\-]+)', header_str)
    if match:
        # Определяем формат даты: если в строке есть тире, то используем формат ISO, иначе – формат с точками.
        date_format = "%Y-%m-%d" if "-" in match.group(1) else "%d.%m.%Y"
        report_start = pd.to_datetime(match.group(1), format=date_format)
        report_end = pd.to_datetime(match.group(2), format=date_format)
        return report_start, report_end
    else:
        st.error("Не удалось извлечь отчетный период из первой строки файла с метками.")
        return pd.NaT, pd.NaT

# Интерфейс загрузки файлов в Streamlit
st.title("Генератор еженедельных отчётов")

mp_file = st.file_uploader("Загрузите файл с медиапланом", type=["xlsx"])
metki_file = st.file_uploader("Загрузите файл с метками UTM", type=["xlsx"])

if mp_file and metki_file:
    # Загружаем медиаплан с поиском заголовка, содержащего '№'
    df_mp = load_excel_with_custom_header(mp_file, '№')
    # Если первый столбец медиаплана полностью пустой, удаляем его
    if df_mp.iloc[:, 0].isna().all():
        df_mp = df_mp.iloc[:, 1:]
    st.write("Медиаплан:", df_mp.head())
    
    # Извлекаем отчетный период из файла с метками (из первой строки)
    report_start, report_end = extract_report_period(metki_file)
    st.write("Отчетный период:", report_start, report_end)
    
    # Загружаем файл с метками с поиском заголовка, содержащего 'UTM Source'
    df_metki = load_excel_with_custom_header(metki_file, 'UTM Source')
    st.write("Метки UTM:", df_metki.head())
    
    # Вводим количество первичных и целевых обращений
    tp_primary_calls = st.number_input("Тематические площади: первичные обращения", min_value=0, step=1)
    tp_target_calls = st.number_input("Тематические площади: ЦО", min_value=0, step=1)
    oh_primary_calls = st.number_input("Охватное размещение: первичные обращения", min_value=0, step=1)
    oh_target_calls = st.number_input("Охватное размещение: ЦО", min_value=0, step=1)

        # Функция для извлечения начальной и конечной даты
    def extract_dates(period):
        start_date, end_date = period.split('-')
        start_date = pd.to_datetime(start_date.strip(), format='%d.%m.%Y')
        end_date = pd.to_datetime(end_date.strip(), format='%d.%m.%Y')
        return start_date, end_date

# Применение функции и создание новых столбцов с начальной и конечной датой
    df[['Start Date', 'End Date']] = df['Период'].apply(extract_dates).apply(pd.Series)
# Бюджет по неделям
    def calculate_budget_per_week(row):
        start_date = row['Start Date']
        end_date = row['End Date']

    # Определяем границы периода с учетом полных недель
        first_monday = start_date - pd.Timedelta(days=start_date.weekday())  # Понедельник первой недели
        last_sunday = end_date + pd.Timedelta(days=(6 - end_date.weekday()))  # Воскресенье последней недели

        weeks = []
        week_start = first_monday

        while week_start <= last_sunday:
            week_end = week_start + pd.Timedelta(days=6)  # Воскресенье

        # Определяем активный период в рамках недели
            active_start = max(week_start, start_date)  # Либо понедельник, либо старт кампании
            active_end = min(week_end, end_date)  # Либо воскресенье, либо конец кампании

            active_days = (active_end - active_start).days + 1  # Количество активных дней кампании в неделе
            total_days = (end_date - start_date).days + 1  # Все активные дни кампании

        # Если в неделе нет активных дней кампании, бюджет = 0
            week_budget = row['Общая стоимость с учетом НДС и АК'] * (active_days / total_days) if active_days > 0 else 0

        # Добавляем данные
            weeks.append((week_start, week_end, week_budget))

        # Переход к следующей неделе
            week_start += pd.Timedelta(days=7)

        return weeks
    
    # Применение функции для всех строк
    week_budget_data = []
    for idx, row in df.iterrows():
        week_budget_data.extend(calculate_budget_per_week(row))

    # Создаём DataFrame для распределённых бюджетов по неделям
    df_week_budget = pd.DataFrame(week_budget_data, columns=['Неделя с', 'Неделя по', 'Бюджет на неделю'])

    # Добавляем информацию о сайте и периоде для каждой недели
    df_week_budget['Название сайта'] = np.repeat(df['Название сайта'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])
    df_week_budget['Категория'] = np.repeat(df['Категория'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])
   
    # Группировка по категории и неделе, суммирование бюджета
    df_weekly_category_budget = df_week_budget.groupby(['Категория', 'Неделя с', 'Неделя по'], as_index=False)['Бюджет на неделю'].sum()
    
    # Очистка данных в KPI прогноз
    df['KPI прогноз'] = df['KPI прогноз'].replace("-", np.nan)  # Заменяем "-" на NaN
    df['KPI прогноз'] = pd.to_numeric(df['KPI прогноз'], errors='coerce').fillna(0)  # Конвертируем в числа, заменяем NaN на 0

    def calculate_kpi_per_week(row):
        start_date = row['Start Date']
        end_date = row['End Date']

        # Определяем понедельник перед стартом и воскресенье после окончания
        first_monday = start_date - pd.Timedelta(days=start_date.weekday())  # Понедельник недели старта
        last_sunday = end_date + pd.Timedelta(days=(6 - end_date.weekday()))  # Воскресенье недели окончания

        weeks = []
        week_start = first_monday

        while week_start <= last_sunday:
            week_end = week_start + pd.Timedelta(days=6)  # Воскресенье

            # Определяем, какие дни из недели входят в период кампании
            active_start = max(week_start, start_date)  # Либо понедельник, либо старт кампании
            active_end = min(week_end, end_date)  # Либо воскресенье, либо конец кампании

            active_days = (active_end - active_start).days + 1  # Дни кампании в этой неделе
            total_days = (end_date - start_date).days + 1  # Все активные дни кампании

            # Если в неделе нет активных дней кампании, KPI = 0
            week_kpi = round(row['KPI прогноз'] * (active_days / total_days)) if active_days > 0 else 0

            # Добавляем неделю в список
            weeks.append((week_start, week_end, week_kpi))

            # Переход к следующей неделе
            week_start += pd.Timedelta(days=7)

        return weeks
    
    # Функция для корректного распределения KPI по неделям

    # Применяем к каждому ряду в df
    week_kpi_data = []
    for idx, row in df.iterrows():
        week_kpi_data.extend(calculate_kpi_per_week(row))
    
    # Создаем DataFrame для KPI
    df_week_kpi = pd.DataFrame(week_kpi_data, columns=['Неделя с', 'Неделя по', 'KPI на неделю'])
    
    # Добавляем категорию и сайт
    df_week_kpi['Категория'] = np.repeat(df['Категория'].values, [len(calculate_kpi_per_week(row)) for _, row in df.iterrows()])
    df_week_kpi['Название сайта'] = np.repeat(df['Название сайта'].values, [len(calculate_kpi_per_week(row)) for _, row in df.iterrows()])

    # Группировка KPI по категориям и неделям
    df_weekly_category_kpi = df_week_kpi.groupby(['Категория', 'Неделя с', 'Неделя по'], as_index=False)['KPI на неделю'].sum()
    
    # Обрабатываем UTM-метки
    df_raw = load_excel(metki_file, header=None)
    header_str = str(df_raw.iloc[0, 0])
    match = re.search(r'Отчет за период с (\d{4}-\d{2}-\d{2}) по (\d{4}-\d{2}-\d{2})', header_str)
    if match:
        report_start = pd.to_datetime(match.group(1))
        report_end = pd.to_datetime(match.group(2))
    else:
        st.error("Не удалось извлечь период из заголовка!")

    # Фильтрация меток
    df_filtered = df_metki[df_metki['UTM Campaign'].astype(str).str.contains('arwm', na=False, case=False)]
    df_filtered = df_filtered[~df_filtered['UTM Source'].astype(str).isin(['yandex_maps', 'navigator'])]

    # Вычисления
    df_filtered['Время на сайте'] = pd.to_timedelta(df_filtered['Время на сайте'])
    total_visits = df_filtered['Визиты'].sum()
    total_visitors = df_filtered['Посетители'].sum()
    
    weighted_avg_otkazy = (df_filtered['Отказы'] * df_filtered['Визиты']).sum() / total_visits
    weighted_avg_glubina = (df_filtered['Глубина просмотра'] * df_filtered['Визиты']).sum() / total_visits
    weighted_avg_robotnost = (df_filtered['Роботность'] * df_filtered['Визиты']).sum() / total_visits
    weighted_avg_time_sec = (df_filtered['Время на сайте'].dt.total_seconds() * df_filtered['Визиты']).sum() / total_visits

    def format_seconds(total_seconds):
        total_seconds = int(total_seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    weighted_avg_time_str = format_seconds(weighted_avg_time_sec)
 
    # Приводим даты к нужному формату
    df_week_budget['Неделя с'] = pd.to_datetime(df_week_budget['Неделя с'])
    df_week_budget['Неделя по'] = pd.to_datetime(df_week_budget['Неделя по'])
    
# Дополнительный код начало
    
    # Группировка данных по UTM Source с расчётом взвешенных средних
    utm_summary = df_filtered.groupby("UTM Source").agg({
        "Визиты": "sum",
        "Посетители": "sum"
    }).reset_index()

    # Добавляем расчёт взвешенных средних для показателей
    utm_summary["Отказы"] = utm_summary["UTM Source"].apply(
        lambda source: (df_filtered.loc[df_filtered["UTM Source"] == source, "Отказы"] * 
                        df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"]).sum() / 
                       df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"].sum()
    )

    utm_summary["Глубина просмотра"] = utm_summary["UTM Source"].apply(
        lambda source: (df_filtered.loc[df_filtered["UTM Source"] == source, "Глубина просмотра"] * 
                        df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"]).sum() / 
                       df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"].sum()
    )

    utm_summary["Роботность"] = utm_summary["UTM Source"].apply(
        lambda source: (df_filtered.loc[df_filtered["UTM Source"] == source, "Роботность"] * 
                        df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"]).sum() / 
                       df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"].sum()
    )

    utm_summary["Время на сайте (сек)"] = utm_summary["UTM Source"].apply(
        lambda source: (df_filtered.loc[df_filtered["UTM Source"] == source, "Время на сайте"].dt.total_seconds() * 
                        df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"]).sum() / 
                       df_filtered.loc[df_filtered["UTM Source"] == source, "Визиты"].sum()
    )

    # Преобразуем среднее время в ЧЧ:ММ:СС
    utm_summary["Время на сайте"] = utm_summary["Время на сайте (сек)"].apply(format_seconds)
    utm_summary.drop(columns=["Время на сайте (сек)"], inplace=True)

    # Проверяем условия и формируем предупреждения
    warnings = []
    for _, row in utm_summary.iterrows():
        if row["Отказы"] > 0.35:
            warnings.append(f"⚠ Высокий процент отказов ({row['Отказы']:.2%}) для источника {row['UTM Source']}")
        if row["Роботность"] > 0.10:
            warnings.append(f"⚠ Высокая роботность ({row['Роботность']:.2%}) для источника {row['UTM Source']}")
        if pd.to_timedelta(row["Время на сайте"]) < pd.Timedelta(minutes=1):
            warnings.append(f"⚠ Низкое время на сайте ({row['Время на сайте']}) для источника {row['UTM Source']}")
    # Доп код конец
    
    # Проверяем диапазон дат
    report_week_df = df_weekly_category_budget[
        (df_weekly_category_budget['Неделя с'] <= report_end) & (df_weekly_category_budget['Неделя по'] >= report_start)
    ]

        # Проверяем диапазон дат
    report_week_df_kpi = df_weekly_category_kpi[
        (df_weekly_category_kpi['Неделя с'] <= report_end) & (df_weekly_category_kpi['Неделя по'] >= report_start)
    ]

    # Извлекаем бюджет для категорий, содержащих слово "тема" для Тематических площадок
    tp_budget = report_week_df.loc[report_week_df['Категория'].str.strip().str.contains('тема', case=False, na=False), 'Бюджет на неделю'].sum()

    # Извлекаем бюджет для категорий, содержащих слово "охват" для Охватного размещения
    oh_budget = report_week_df.loc[report_week_df['Категория'].str.strip().str.contains('охват', case=False, na=False), 'Бюджет на неделю'].sum()

    # Извлекаем KPI для "Тематических площадок" и "Охватного размещения"
    kpi_tp = report_week_df_kpi.loc[report_week_df_kpi['Категория'].str.strip().str.contains('тема', case=False, na=False), 'KPI на неделю'].sum()
    kpi_oh = report_week_df_kpi.loc[report_week_df_kpi['Категория'].str.strip().str.contains('охват', case=False, na=False), 'KPI на неделю'].sum()

    # Проверяем, что KPI прогноз не NaN
    if pd.notna(kpi_tp) and kpi_tp != 0:  # Проверка на NaN и 0
        tp_status = f"{((tp_target_calls - kpi_tp) / kpi_tp) * 100 + 100:.0f} %" if pd.notna(tp_target_calls) else "0 %"
    else:
        tp_status = "100 %"

    if pd.notna(kpi_oh) and kpi_oh != 0:  # Проверка на NaN и 0
        oh_status = f"{((oh_target_calls - kpi_oh) / kpi_oh) * 100 + 100:.0f} %" if pd.notna(oh_target_calls) else "0 %"
    else:
        oh_status = "100 %"

    # Рассчитываем CPL для первичных обращений
    tp_cpl = tp_budget / tp_primary_calls if tp_primary_calls > 0 else 0
    oh_cpl = oh_budget / oh_primary_calls if oh_primary_calls > 0 else 0

    # Приводим к строковому формату
    tp_budget_str = f"{tp_budget:,.2f}".replace(',', ' ') if tp_budget > 0 else "0"
    oh_budget_str = f"{oh_budget:,.2f}".replace(',', ' ') if oh_budget > 0 else "0"
    tp_cpl_str = f"{tp_cpl:,.2f}".replace(',', ' ') if tp_cpl > 0 else "0"
    oh_cpl_str = f"{oh_cpl:,.2f}".replace(',', ' ') if oh_cpl > 0 else "0"

    # Генерация отчёта
    report_text = f"""
    Медийная реклама ({report_start.strftime('%d.%m.%y')}-{report_end.strftime('%d.%m.%y')})

    Тематические площадки:
    Выполнение по бюджету плановое ({tp_budget_str} ₽ с НДС)
    Первичные обращения — {tp_primary_calls}
    CPL (первичных обращений) — {tp_cpl_str} ₽ с НДС
    ЦО — {tp_target_calls}
    Выполнение плана ЦО: {tp_status}

    Охват:
    Выполнение по бюджету плановое ({oh_budget_str} ₽ с НДС)
    Первичные обращения — {oh_primary_calls}
    CPL (первичных обращений) — {oh_cpl_str} ₽ с НДС
    Целевые обращения — {oh_target_calls}
    Выполнение плана ЦО: {oh_status}

    Метрики:
    - Выполнение плана по бюджету 100%
    - Отказы: {weighted_avg_otkazy * 100:.2f}%
    - Глубина просмотра: {weighted_avg_glubina:.2f}
    - Время на сайте: {weighted_avg_time_str}
    - Роботность: {weighted_avg_robotnost * 100:.2f}%

    Плановые работы:
    - Следить за динамикой
    """

    # Вывод предупреждений
    if warnings:
        st.subheader("⚠ Предупреждения")
        for warning in warnings:
            st.warning(warning)
    
    # Вывод данных в Streamlit
    st.subheader("Еженедельный отчет")
    st.text_area(report_text, report_text, height=100)
    
    # Вывод таблицы с агрегированными данными
    st.subheader("Анализ по UTM Source")
    st.dataframe(utm_summary)

    st.subheader("Фильтрованные UTM-данные")
    st.dataframe(df_filtered)

    st.subheader("Поведенческие показатели Медийной РК")
    st.dataframe(pd.DataFrame({
        'Время на сайте': [weighted_avg_time_str],
        'Отказы': [weighted_avg_otkazy],
        'Глубина просмотра': [weighted_avg_glubina],
        'Роботность': [weighted_avg_robotnost]
    }))

    st.subheader("Распределение бюджета по неделям")
    st.dataframe(df_weekly_category_budget)

    st.subheader("Распределение KPI по неделям")
    st.dataframe(df_week_kpi)
    
    # Проверяем, что строки найдены
    if report_week_df.empty:
        st.error("Ошибка: не найден бюджет для указанного периода!")
        st.write("Доступные даты:", df_week_budget[['Неделя с', 'Неделя по']].drop_duplicates())
    else:
        st.write("Найденные данные:", report_week_df)

    # Проверяем tp_budget
    st.write(f"tp_budget: {tp_budget}, oh_budget: {oh_budget}")

    # Выводим строки для проверки
    st.write(report_week_df)

    # Проверяем cpl
    st.write(f"tp_cpl: {tp_cpl}, oh_cpl: {oh_cpl}")

    # Далее продолжаем с расчетами
