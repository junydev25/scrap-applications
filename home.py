import streamlit as st
from pathlib import Path
from database import load_json_to_database

st.set_page_config(page_title="홈")

json_path = Path(".") / "datasets/registration.json"
load_json_to_database(json_path)

# 앱 실행 시 자동으로 Login 페이지로 이동
st.switch_page("pages/login.py")