# app.py
import streamlit as st
from getdata import fetch_activist_data
from generatestory import generate_storyboard
from generateprompts import generate_image_prompts

st.set_page_config(page_title="독립운동가 웹툰 에이전트", page_icon="📜", layout="centered")

st.title("📜 독립운동가 웹툰 제작 에이전트")

# 세션 상태(Session State) 초기화: 검색된 명단 데이터를 메모리에 저장하기 위함
if 'activists_list' not in st.session_state:
    st.session_state['activists_list'] = []

gemini_key_input = st.text_input("Gemini API 키를 입력하세요:", type="password")

st.subheader("1. 독립운동 계열 선택 및 명단 검색")

movement_dict = {
    "3.1운동": "AA",
    "3.1운동지원": "AB",
    "계몽운동": "AC",
    "광복군": "AE",
    "국내항일": "AG",
    "만주방면": "AJ",
    "의병": "AN",
    "의열투쟁": "AO",
    "임시정부": "AR",
    "학생운동": "AU"
}

def extract_items_safely(parsed_dict: dict) -> list:
    """
    제공된 실제 XML 구조(<root> -> <item>)에 맞춘 안전한 파싱 함수
    """
    try:
        # 실제 데이터 구조에 맞게 'root' 안의 'item'을 직관적으로 타겟팅
        items = parsed_dict.get('root', {}).get('item', None)
        
        # 데이터가 없는 경우 방어 로직
        if not items:
            return []
            
        # 검색 결과가 1건일 경우 dict로 반환되는 xmltodict의 특성을 방어하여 list로 통일
        if isinstance(items, dict):
            return [items]
        elif isinstance(items, list):
            return items
        else:
            return []
            
    except Exception as e:
        print(f"데이터 파싱 중 에러 발생: {e}")
        return []

selected_movement_name = st.selectbox("검색할 운동 계열을 선택해주세요:", list(movement_dict.keys()))
selected_code = movement_dict[selected_movement_name]

# 1단계 버튼: 데이터 검색 후 세션에 저장만 수행
if st.button("해당 계열 독립운동가 명단 검색"):
    with st.spinner('공공데이터 서버와 통신하고 있습니다...'):
        raw_xml, parsed_dict = fetch_activist_data(movement_code=selected_code)
        
        if parsed_dict and "error" not in parsed_dict:
            # 새로 작성한 안전한 파싱 함수 적용
            items = extract_items_safely(parsed_dict)
            
            if items:
                st.session_state['activists_list'] = items
                st.success(f"총 {len(items)}명의 데이터를 찾았습니다. 아래에서 인물을 선택하세요.")
            else:
                st.error("XML 데이터 파싱 완료. 하지만 해당 계열에 등록된 인물 데이터(item)가 없습니다.")
                st.session_state['activists_list'] = []
                # 구조 확인을 위해 원본 XML 일부를 화면에 출력 (디버깅용)
                with st.expander("원본 XML 구조 확인 (문제 발생 시 확인용)"):
                    st.code(raw_xml[:1000], language="xml")
        else:
            st.error("공공데이터를 정상적으로 가져오지 못했습니다.")

# 세션에 데이터가 있을 경우에만 2단계 화면(인물 선택 및 대본 생성) 출력
if st.session_state['activists_list']:
    st.write("---")
    st.subheader("2. 웹툰의 주인공을 선택하세요")
    
    # Fact: API마다 이름과 업적의 태그명이 다릅니다. (예: nameKo, content, workDesc 등)
    # 딕셔너리의 .get() 메서드를 여러 개 체이닝하여 어떤 태그명이든 유연하게 가져오도록 수정
    options = []
    for person in st.session_state['activists_list']:
        # 이름 태그 후보 탐색
        p_name = person.get('nameKo') or person.get('name') or person.get('이름') or "이름불명"
        # 업적 태그 후보 탐색
        p_activity = person.get('activities') or person.get('workDesc') or "내용없음"
        
        # 텍스트가 너무 길면 UI가 깨지므로 30자로 자름 > 70자로 수정
        display_text = f"{p_name} - {str(p_activity)[:70]}"
        options.append(display_text)
    
    selected_index = st.selectbox("인물 선택:", range(len(options)), format_func=lambda x: options[x])
    selected_person_data = st.session_state['activists_list'][selected_index]
    
    #st.write("### 📌 선택한 인물 데이터")
    #st.json(selected_person_data)

    # 2단계 버튼: 선택한 단일 인물의 데이터로 스토리 생성
    if st.button("선택한 인물로 스토리보드 생성 시작"):
        if not gemini_key_input:
            st.warning("Gemini API 키를 먼저 입력해주세요.")
        else:
            with st.spinner('선택한 인물의 데이터로 대본을 창작하고 팩트체크 중입니다...'):
                
                # 반환값이 dict 형태로 들어옴
                story_data = generate_storyboard(gemini_api_key=gemini_key_input, parsed_data=selected_person_data)
                
                if story_data and "storyboard" in story_data:
                    
                    st.write("### 👤 캐릭터 외모 설정 (일관성 유지용)")
                    st.info(story_data.get('character_appearance', '외모 정보 처리 누락'))
                    
                    st.write("### 📝 완성된 웹툰 스토리보드 (팩트체크 완료)")
                    for cut in story_data['storyboard']:
                        with st.expander(f"Cut {cut['cut']}"):
                            st.markdown(f"**지문:** {cut['description']}")
                            st.markdown(f"**대사:** {cut['dialogue']}")
                    
                    # 생성된 데이터를 세션에 저장하여 다음 단계에서 활용 가능하게 함
                    st.session_state['current_story_data'] = story_data
                else:
                    st.error("스토리보드 생성에 실패했거나 JSON 구조가 올바르지 않습니다.")

# --- 3단계: 이미지 프롬프트 생성 UI ---

if 'current_story_data' in st.session_state and st.session_state['current_story_data']:
    st.write("---")
    st.subheader("3. 이미지 생성 프롬프트 자동 작성")
    
    if st.button("스토리보드 기반 Animagine XL 4.0 프롬프트 생성"):
        with st.spinner('컷별 Danbooru 태그를 분석하고 생성 중입니다...'):
            story_data = st.session_state['current_story_data']
            
            # 5단계 모듈 호출
            prompts = generate_image_prompts(
                gemini_api_key=gemini_key_input,
                character_appearance=story_data['character_appearance'],
                storyboard=story_data['storyboard']
            )
            
            if prompts:
                st.success("프롬프트 생성이 완료되었습니다.")
                st.session_state['current_prompts'] = prompts # 세션 저장
                
                # 결과 출력
                for p in prompts:
                    with st.container():
                        st.markdown(f"**[Cut {p['cut']}]**")
                        st.code(f"Positive: {p['positive_prompt']}\nNegative: {p['negative_prompt']}", language="text")
            else:
                st.error("프롬프트 생성에 실패했습니다.")