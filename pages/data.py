import streamlit as st
import json
from pathlib import Path
import pandas as pd

st.title("메인 페이지")

@st.cache_data
def load_data():
    json_path = Path(".") / "datasets/registration.json"
    with open (json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return data

if not st.session_state.get("logged_in", False):
    st.warning("먼저 로그인 해주세요.")
    st.switch_page("pages/login.py")  # ✅ 로그인 안 한 경우 강제 이동
else:
    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.switch_page("pages/login.py")
        
    # TODO Refactoring
    # TODO 1. DB로부터 신청 데이터들 가져와야함
    data = load_data()
    
    # TODO 2. 가장 오래된 것부터 정렬
    if "data" not in st.session_state:
        st.session_state.data = sorted(data, key=lambda x:x.get("createDate"), reverse=False)

    st.write("현재 데이터 개수:", len(st.session_state.data))
    
    # TODO 3. 해당 페이지 상단에 10개씩 보여주기(아래의 상세 내역 보여줘야 하기 때문)
    
    # 클릭 상태를 session_state로 관리
    if "clicked_card" not in st.session_state:
        st.session_state.clicked_card = None

    col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
    col1.write("ID")
    col2.write("제목")
    col3.write("작성자")
    col4.write("신청일")
    col5.write("보기")
    st.markdown("---")
    
    idx = None
    for idx, data in enumerate(st.session_state.data[:10]):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
            col1.write(idx+1)
            col2.write(data["title"])
            col3.write(data["author"])
            col4.write(data["createDate"])

            if col5.button("Click", key=f"btn_{data['id']}"):
                st.session_state.clicked_card = idx

            st.markdown("---")

    # TODO 4. 상세 내역(JSON -> Table)
    record = {}
    if st.session_state.clicked_card is not None:
        record = st.session_state.data[st.session_state.clicked_card]
        table_cols = {"id":"신청 번호",
                      "title":"제목",
                      "author":"작성자",
                      "createDate":"신청일",
                      "content":"신청 내용"}
        
        df = pd.DataFrame.from_dict(record, orient="index", columns=["내용"])
        df.index = df.index.map(table_cols)
        df.index_name = "항목"
        df.reset_index()
        st.dataframe(df)
        
        # TODO 5. 보내기(승인 함을 JSON으로 보내는 것)
        # TODO 승인 했다는 것을 JSON에 포함 시킬지 말지는 고민해볼 부분
        if st.button("승인"):
            # 승인 플래그 추가  
            record["approved"] = True
            
            st.session_state.data = [item for item in st.session_state.data if item["id"] != record["id"] and item["author"] != record["author"]]
            st.session_state.clicked_card = None
            
            # 외부로 JSON 타입으로 전송
            st.rerun()
