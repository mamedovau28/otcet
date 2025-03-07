
import streamlit as st
import pandas as pd
import numpy as np
import re
import subprocess

# Устанавливаем openpyxl
subprocess.run(["pip", "install", "openpyxl"], check=True)

# Функция загрузки Excel-файла
@st.cache
def load_excel(file, sheet=0, header=4):
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

    # Функция для извлечения дат
    def extract_dates(period):
        start_date, end_date = period.split('-')
        return pd.to_datetime(start_date.strip(), format='%d.%m.%Y'), pd.to_datetime(end_date.strip(), format='%d.%m.%Y')

    df[['Start Date', 'End Date']] = df['Период'].apply(extract_dates).apply(pd.Series)

    # Функция для расчета бюджета по неделям
    def calculate_budget_per_week(row):
        start_date, end_date = row['Start Date'], row['End Date']
        week_start = start_date - pd.Timedelta(days=start_date.weekday())
        weeks = []
        while week_start <= end_date:
            week_end = week_start + pd.Timedelta(days=6)
            if week_end > end_date:
                week_end = end_date
            days_in_week = (week_end - week_start).days + 1
            total_days = (end_date - start_date).days + 1
            week_budget = row['Общая стоимость с учетом НДС и АК'] * (days_in_week / total_days)
            weeks.append((week_start, week_end, week_budget))
            week_start = week_end + pd.Timedelta(days=1)
        return weeks

    # Применение расчета бюджета по неделям
    week_budget_data = []
    for _, row in df.iterrows():
        week_budget_data.extend(calculate_budget_per_week(row))

    df_week_budget = pd.DataFrame(week_budget_data, columns=['Неделя с', 'Неделя по', 'Бюджет на неделю'])
    df_week_budget['№'] = np.repeat(df['№'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])
    df_week_budget['Название сайта'] = np.repeat(df['Название сайта'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])
    df_week_budget['Категория'] = np.repeat(df['Категория'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])
    df_week_budget['KPI прогноз'] = np.repeat(df['KPI прогноз'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])
    df_week_budget['Период'] = np.repeat(df['Период'].values, [len(calculate_budget_per_week(row)) for _, row in df.iterrows()])

    # Группировка бюджета по категориям и неделям
    df_weekly_category_budget = df_week_budget.groupby(['Категория', 'Неделя с', 'Неделя по'], as_index=False)['Бюджет на неделю'].sum()

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

    # Проверяем диапазон дат
    if 'report_start' in locals() and 'report_end' in locals():
        report_week_df = df_week_budget[
            (df_week_budget['Неделя с'] <= report_end) & (df_week_budget['Неделя по'] >= report_start)
        ]

        # Проверяем, что строки найдены
        if report_week_df.empty:
            st.error("Ошибка: не найден бюджет для указанного периода!")
            st.write("Доступные даты:", df_week_budget[['Неделя с', 'Неделя по']].drop_duplicates())
        else:
            st.write("Найденные данные:", report_week_df)

            # Извлекаем бюджет для "Тематических площадок" и "Охватного размещения"
            tp_budget = report_week_df.loc[report_week_df['Категория'] == 'Тематические площадки', 'Бюджет на неделю'].sum()
            oh_budget = report_week_df.loc[report_week_df['Категория'] == 'Охватное размещение', 'Бюджет на неделю'].sum()

            # Проверка на NaN
            tp_budget = tp_budget if not np.isnan(tp_budget) else 0
            oh_budget = oh_budget if not np.isnan(oh_budget) else 0

            # Приводим к строковому формату
            tp_budget_str = f"{tp_budget:,.2f}".replace(',', ' ') if tp_budget > 0 else "0"
            oh_budget_str = f"{oh_budget:,.2f}".replace(',', ' ') if oh_budget > 0 else "0"

            # Форматируем даты в нужный вид (дд.мм-дд.мм)
            report_period_str = f"{report_start.strftime('%d.%m')}-{report_end.strftime('%d.%m')}"

            # Подстановка в отчёт
            report_text = f"""
Медийная реклама {report_period_str}

Тематические площадки:
Выполнение по бюджету плановое ({tp_budget_str} ₽ с НДС)
Первичные обращения — { 'нет данных' }
Целевые обращения — { 'нет данных' }
CPL (первичных обращений) — { 'нет данных' } ₽ с НДС

Охват:
Выполнение по бюджету плановое ({oh_budget_str} ₽ с НДС)
Первичные обращения — { 'нет данных' }
Целевые обращения — { 'нет данных' }
CPL (первичных обращений) — { 'нет данных' } ₽ с НДС

Комментарий:
Расход на дату — 100 %
Отказы — {weighted_avg_otkazy_pct:.2f} %
Глубина просмотра — {weighted_avg_glubina:.2f}
Время на сайте — {weighted_avg_time_str}
Роботность — {weighted_avg_robotnost_pct:.2f} %

Проделанные работы:
- Запуск РК
- Написали площадкам по оптимизации РК

Плановые работы:
- Следить за динамикой открута и выполнением по ЦО
"""

            # Вывод данных в Streamlit
            st.subheader("Распределение бюджета по неделям")
            st.dataframe(df_weekly_category_budget)

            st.subheader("Фильтрованные UTM-данные")
            st.dataframe(df_filtered)

            st.subheader("Сводные показатели")
            st.dataframe(pd.DataFrame({
                'визиты': [total_visits],
                'посетители': [total_visitors],
                'время на сайте': [weighted_avg_time_str]
            }))

            st.subheader("Отчёт")
            st.text_area("Сформированный отчёт", report_text, height=300)
    else:
        st.error("Ошибка: не удалось извлечь период из заголовка UTM-меток!")
