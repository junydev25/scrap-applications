import streamlit as st

st.set_page_config(page_title="홈")

# 앱 실행 시 자동으로 Login 페이지로 이동
st.switch_page("pages/login.py")