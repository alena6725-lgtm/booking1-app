import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

from st_aggrid import AgGrid, GridOptionsBuilder

EXCEL_FILE = "bookings.xlsx"

russian_cities = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Нижний Новгород",
    "Казань", "Челябинск", "Омск", "Самара", "Ростов-на-Дону", "Уфа", "Красноярск",
    "Воронеж", "Пермь", "Волгоград", "Краснодар", "Саратов", "Тюмень", "Тольятти",
]

professional_roles = [
    "Разработчик", "Тестировщик", "Менеджер проектов", "Аналитик", "Дизайнер",
    "DevOps инженер", "Аналитик данных", "Бизнес-аналитик", "Менеджер по продукту",
    "HR", "Маркетолог", "Системный администратор", "Инженер по качеству",
    "Технический писатель", "Архитектор ПО", "QA инженер", "Frontend разработчик",
    "Backend разработчик", "Fullstack разработчик",
]

def load_bookings():
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            return df
        except:
            return pd.DataFrame()
    else:
        columns = [
            "Дата рассылки", "№", "Название компании", "Ответственный за бронь",
            "Регион(ы)", "Профобласть / Роль", "Название вакансии", "Ссылка на вакансию",
            "Ссылка на jira", "Комментарий",
            "Ответственный за отправку рассылки", "Ссылка на продукт в crm"
        ]
        return pd.DataFrame(columns=columns)

def save_bookings(df):
    df.to_excel(EXCEL_FILE, index=False)

def parse_list_field(field: str):
    if not field:
        return set()
    return set([v.strip().lower() for v in str(field).split(",")])

def has_intersection(set1: set, set2: set):
    return len(set1.intersection(set2)) > 0

def check_conflict(existing_row, region_target, prof_target):
    regions_exist = parse_list_field(existing_row["Регион(ы)"])
    profs_exist = parse_list_field(existing_row["Профобласть / Роль"])
    return has_intersection(regions_exist, region_target) and has_intersection(profs_exist, prof_target)

def can_book_on_date(bookings_df, date_str, region_target, prof_target):
    day_bookings = bookings_df[bookings_df["Дата рассылки"] == date_str]
    if len(day_bookings) >= 13:
        return False
    for _, row in day_bookings.iterrows():
        if check_conflict(row, region_target, prof_target):
            return False
    return True

def find_available_dates(bookings_df, region_str, prof_str, days_ahead=14):
    region_target = parse_list_field(region_str)
    prof_target = parse_list_field(prof_str)

    start_date = datetime.today()

    available_dates = []
    for i in range(days_ahead):
        day = start_date + timedelta(days=i)
        if day.weekday() in [1, 2, 3]:  # Вторник=1, Среда=2, Четверг=3
            day_str = day.strftime("%Y-%m-%d")
            if can_book_on_date(bookings_df, day_str, region_target, prof_target):
                available_dates.append(day_str)
    return available_dates

st.title("Бронирование рассылок")

if "bookings" not in st.session_state:
    st.session_state.bookings = load_bookings()

selected_regions = st.multiselect("Выберите регион(ы)", russian_cities)
selected_profiles = st.multiselect("Выберите профобласть / роль", professional_roles)

if selected_regions and selected_profiles:
    available_dates = find_available_dates(
        st.session_state.bookings,
        ", ".join(selected_regions),
        ", ".join(selected_profiles),
        days_ahead=14
    )

    if available_dates:
        booking_date = st.selectbox("Выберите дату рассылки", available_dates)
    else:
        booking_date = None
        st.warning("Нет доступных дат для выбранного таргетинга.")

    with st.form("booking_form"):
        company = st.text_input("Название компании")
        responsible_booking = st.text_input("Ответственный за бронь")
        vacancy_name = st.text_input("Название вакансии")
        vacancy_link = st.text_input("Ссылка на вакансию")
        jira_link = st.text_input("Ссылка на Jira")
        comment = st.text_area("Комментарий")
        responsible_sending = st.text_input("Ответственный за отправку рассылки")
        crm_link = st.text_input("Ссылка на продукт в CRM")

        submitted = st.form_submit_button("Забронировать")

        if submitted:
            if not booking_date:
                st.error("Выберите дату рассылки")
            elif not company or not responsible_booking:
                st.error("Поля 'Название компании' и 'Ответственный за бронь' обязательны")
            else:
                if can_book_on_date(st.session_state.bookings, booking_date,
                                    parse_list_field(", ".join(selected_regions)),
                                    parse_list_field(", ".join(selected_profiles))):
                    new_nr = len(st.session_state.bookings) + 1
                    new_row = {
                        "Дата рассылки": booking_date,
                        "№": new_nr,
                        "Название компании": company,
                        "Ответственный за бронь": responsible_booking,
                        "Регион(ы)": ", ".join(selected_regions),
                        "Профобласть / Роль": ", ".join(selected_profiles),
                        "Название вакансии": vacancy_name,
                        "Ссылка на вакансию": vacancy_link,
                        "Ссылка на jira": jira_link,
                        "Комментарий": comment,
                        "Ответственный за отправку рассылки": responsible_sending,
                        "Ссылка на продукт в crm": crm_link
                    }
                    st.session_state.bookings = pd.concat([st.session_state.bookings, pd.DataFrame([new_row])], ignore_index=True)
                    save_bookings(st.session_state.bookings)
                    st.success(f"Бронь успешно добавлена на {booking_date}")
                else:
                    st.error("Выбранная дата недоступна из-за пересечений или переполненности.")
else:
    st.info("Пожалуйста, выберите регион(ы) и профобласть/роль для поиска доступных дат.")

st.subheader("Все бронирования")

# ---- Отображение таблицы через AgGrid ----

gb = GridOptionsBuilder.from_dataframe(st.session_state.bookings)
gb.configure_pagination(enabled=True)
gb.configure_side_bar()
gb.configure_default_column(editable=False, groupable=True, filterable=True)
gridOptions = gb.build()

AgGrid(
    st.session_state.bookings,
    gridOptions=gridOptions,
    height=400,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=True,
)
