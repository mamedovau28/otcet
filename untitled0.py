
import subprocess
import streamlit as st
import pandas as pd
import numpy as np
import re

# Функция загрузки Excel-файлов
@st.cache_data
def load_excel(file, sheet=0, header=0):
    return pd.read_excel(file, sheet_name=sheet, header=header)

# Интерфейс загрузки файлов
st.title("Генератор отчётов по медиаплану")

mp_file = st.file_uploader("Загрузите файл с медиапланом", type=["xlsx"])
metki_file = st.file_uploader("Загрузите файл с метками UTM", type=["xlsx"])

if mp_file and metki_file:
    # Читаем файлы
    df_mp = load_excel(mp_file, header=4)
    df_metki = load_excel(metki_file, header=5)

    # Обрабатываем медиаплан
    df = df_mp[['№', 'Название сайта', 'Период', 'Общая стоимость с учетом НДС и АК', 'KPI прогноз']].copy()
    df = df.replace('-', '0')
    df['Категория'] = df['Название сайта'].where(df['№'].isna()).ffill()
    df = df[~df['Период'].isna()]

        # Функция для извлечения начальной и конечной даты
    def extract_dates(period):
        start_date, end_date = period.split('-')
        start_date = pd.to_datetime(start_date.strip(), format='%d.%m.%Y')
        end_date = pd.to_datetime(end_date.strip(), format='%d.%m.%Y')
        return start_date, end_date

# Применение функции и создание новых столбцов с начальной и конечной датой
    df[['Start Date', 'End Date']] = df['Период'].apply(extract_dates).apply(pd.Series)

# Функция для корректного распределения бюджета по неделям
    def calculate_budget_per_week(row):
        start_date = row['Start Date']
        end_date = row['End Date']

    # Начинаем с первой недели, которая содержит start_date
        week_start = start_date - pd.Timedelta(days=start_date.weekday())  # Понедельник недели, в которой start_date
        weeks = []
        while week_start <= end_date:
        # Определяем конец недели (воскресенье)
            week_end = week_start + pd.Timedelta(days=6)
        # Если начало недели в прошлом месяце, но есть дни в текущем, берём только текущий месяц
            if week_start.month < start_date.month:
                week_start = start_date  # Сдвигаем начало недели на первый день периода
        # Если конец недели выходит за границы периода, ограничиваем его
            if week_end > end_date:
                week_end = end_date
        # Количество дней, попадающих в период
            days_in_week = (week_end - week_start).days + 1
        # Общие дни в периоде
            total_days = (end_date - start_date).days + 1
        # Пропорциональный бюджет
            week_budget = row['Общая стоимость с учетом НДС и АК'] * (days_in_week / total_days)
        # Добавляем данные
            weeks.append((week_start, week_end, week_budget))
        # Следующая неделя
            week_start = week_end + pd.Timedelta(days=1)
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

    # Функция для корректного распределения бюджета по неделям
    def calculate_kpi_per_week(row):
        start_date = row['Start Date']
        end_date = row['End Date']

    # Начинаем с первой недели, которая содержит start_date
        week_start = start_date - pd.Timedelta(days=start_date.weekday())  # Понедельник недели, в которой start_date
        weeks = []
        while week_start <= end_date:
        # Определяем конец недели (воскресенье)
            week_end = week_start + pd.Timedelta(days=6)
        # Если начало недели в прошлом месяце, но есть дни в текущем, берём только текущий месяц
            if week_start.month < start_date.month:
                week_start = start_date  # Сдвигаем начало недели на первый день периода
        # Если конец недели выходит за границы периода, ограничиваем его
            if week_end > end_date:
                week_end = end_date
        # Количество дней, попадающих в период
            days_in_week = (week_end - week_start).days + 1
        # Общие дни в периоде
            total_days = (end_date - start_date).days + 1
        # Пропорциональный KPI
            week_kpi = round(row['KPI прогноз'] * (days_in_week / total_days), 1)
        # Добавляем данные
            weeks.append((week_start, week_end, week_kpi))
        # Следующая неделя
            week_start = week_end + pd.Timedelta(days=1)
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

    # Извлекаем бюджет для "Тематических площадок" и "Охватного размещения"
    tp_budget = report_week_df.loc[report_week_df['Категория'] == 'Тематические площадки', 'Бюджет на неделю'].sum()
    oh_budget = report_week_df.loc[report_week_df['Категория'] == 'Охватное размещение', 'Бюджет на неделю'].sum()

    # Извлекаем KPI для "Тематических площадок" и "Охватного размещения"
    kpi_tp = report_week_df_kpi.loc[report_week_df_kpi['Категория'] == 'Тематические площадки','KPI на неделю'].sum()
    kpi_oh = report_week_df_kpi.loc[report_week_df_kpi['Категория'] == 'Охватное размещение','KPI на неделю'].sum()

    # Вводим количество первичных и целевых обращений
    tp_primary_calls = st.number_input("Введите количество: Первичных обращений для Тематических площадок", min_value=0, step=1)
    tp_target_calls = st.number_input("Введите количество: ЦО для Тематических площадок", min_value=0, step=1)
    oh_primary_calls = st.number_input("Введите количество: Первичных обращений для Охватного размещения", min_value=0, step=1)
    oh_target_calls = st.number_input("Введите количество: ЦО для Охватного размещения", min_value=0, step=1)

    # Выводим значения после их определения
    st.write(f"oh_target_calls: {oh_target_calls}, kpi_oh: {kpi_oh}")

    # Вычисление отклонения по проценту от KPI прогноза
    tp_status = f"{((tp_target_calls - kpi_tp) / kpi_tp) * 100:.1f}%" if kpi_tp == nan else "100%"
    oh_status = f"{((oh_primary_calls - kpi_oh) / kpi_oh) * 100:.1f}%" if kpi_tp == nan else "100%"

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
    Выполнение по ЦО плановое: {tp_status}

    Охват:
    Выполнение по бюджету плановое ({oh_budget_str} ₽ с НДС)
    Первичные обращения — {oh_primary_calls}
    CPL (первичных обращений) — {oh_cpl_str} ₽ с НДС
    Целевые обращения — {oh_target_calls}
    Выполнение по ЦО плановое: {oh_status}

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

    # Проверяем, что строки найдены
    if report_week_df_kpi.empty:
        st.error("Ошибка: не найден бюджет для указанного периода!")
        st.write("Доступные даты:", df_weekly_category_kpi[['Неделя с', 'Неделя по']].drop_duplicates())
    else:
        st.write("Найденные данные:", df_weekly_category_kpi)
