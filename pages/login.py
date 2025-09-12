import streamlit as st
USER_CREDENTIALS = {"admin": "1234", "user": "abcd"}

def login(username, password):
    # TODO Refactoring
    # 1. DB에 해당 username이 있는지 확인
    # 2. 있다면 True, 없다면 False 반환
    return USER_CREDENTIALS.get(username) == password

st.title("로그인 페이지")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

with st.form("login_form"):
    username = st.text_input("아이디")
    password = st.text_input("비밀번호", type="password")
    submitted = st.form_submit_button("로그인")

    if submitted:
        if login(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"{username}님 로그인 성공!")

            # ✅ 로그인 성공 시 data.py로 자동 이동
            st.switch_page("pages/data.py")
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
