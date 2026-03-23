import streamlit as st
import datetime

# 화면 기본 설정
st.set_page_config(page_title="독립운동가 웹툰 에이전트", page_icon="📜", layout="centered")

# 메인 타이틀
st.title("📜 독립운동가 웹툰 제작 에이전트")
st.markdown("날짜를 입력하면 해당 날짜와 관련된 독립운동가 데이터를 수집하여 웹툰을 제작합니다.")

# 1단계: 날짜 입력 UI (달력 위젯)
st.subheader("1. 날짜 선택")
selected_date = st.date_input(
    "검색할 날짜를 선택해주세요:",
    value=datetime.date(1919, 3, 1), # 기본값: 1919년 3월 1일
    min_value=datetime.date(1800, 1, 1),
    max_value=datetime.date.today()
)

# 2단계: 관련 독립운동가 표시 및 파이프라인 트리거
if st.button("관련 독립운동가 검색 및 웹툰 제작 시작"):
    
    # 날짜 포맷팅 (예: 1919-03-01 -> 19190301 등 API가 요구하는 형식에 맞춰 변환 대비)
    formatted_date = selected_date.strftime("%Y-%m-%d")
    
    st.success(f"[{formatted_date}] 검색을 시작합니다...")
    
    # ---------------------------------------------------------
    # 가상의 API 호출 결과 (3단계 연동 전 테스트용 데이터)
    # ---------------------------------------------------------
    st.info("Agent가 공공데이터 포털에서 데이터를 수집 중입니다... (가상 연출)")
    
    mock_activists = [
        {"name": "유관순", "activity": "아우내 장터 만세 운동 주도"},
        {"name": "손병희", "activity": "민족대표 33인, 독립선언서 낭독 주도"}
    ]
    
    st.write("### 🔎 검색된 독립운동가 목록")
    for person in mock_activists:
        st.markdown(f"- **{person['name']}**: {person['activity']}")
        
    st.warning("다음 단계: 이 데이터를 바탕으로 LLM 스토리보드 생성이 진행됩니다.")