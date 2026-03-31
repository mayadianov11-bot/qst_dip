import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Анкета", page_icon="📝")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

try:
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open("survey_data").sheet1

except Exception as e:
    st.error("Не удалось подключиться к Google Sheets")
    st.exception(e)
    st.stop()

st.title("Анкета")

with st.form("survey_form"):
    respondent_id = st.text_input("Код респондента")
    age = st.number_input("Возраст", min_value=14, max_value=100, step=1)
    stress = st.slider("Уровень стресса", 0, 10, 5)
    comment = st.text_area("Комментарий")
    submitted = st.form_submit_button("Отправить")

if submitted:
    if not respondent_id.strip():
        st.error("Введите код респондента")
    else:
        try:
            row = [
                datetime.now().isoformat(),
                respondent_id.strip(),
                age,
                stress,
                comment.strip(),
            ]
            sheet.append_row(row)
            st.success("Ответ сохранён")
        except Exception as e:
            st.error("Ошибка при записи в таблицу")
            st.exception(e)