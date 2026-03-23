import streamlit as st

# 분리된 모듈 임포트 (같은 폴더에 해당 .py 파일들이 있어야 함)
import os
import shutil
from PIL import Image
from getdata import fetch_activist_data
from generatestory import generate_storyboard
from generateprompts import generate_image_prompts
from generateimages import queue_comfyui_prompt
from start_server import launch_comfyui_server

def extract_items_safely(parsed_dict: dict) -> list:
    """공공데이터 API의 XML 파싱 결과에서 인물 리스트를 안전하게 추출하는 함수"""
    try:
        items = parsed_dict.get('root', {}).get('item', None)
        if not items:
            return []
        
        if isinstance(items, dict):
            return [items]
        elif isinstance(items, list):
            return items
        else:
            return []
    except Exception as e:
        print(f"데이터 파싱 중 에러 발생: {e}")
        return []

# ==========================================
# 화면 기본 설정 및 세션 초기화
# ==========================================
st.set_page_config(page_title="독립운동가 웹툰 에이전트", page_icon="📜", layout="centered")

st.title("📜 독립운동가 웹툰 제작 에이전트")

# 세션 상태 보존
if 'activists_list' not in st.session_state:
    st.session_state['activists_list'] = []
if 'current_story_data' not in st.session_state:
    st.session_state['current_story_data'] = {}
if 'current_prompts' not in st.session_state:
    st.session_state['current_prompts'] = []

# 공통 API 키 입력
gemini_key_input = st.text_input("Gemini API 키를 입력하세요:", type="password")

# ==========================================
# 1단계: 독립운동 계열 선택 및 명단 검색
# ==========================================
st.subheader("1. 독립운동 계열 선택 및 명단 검색")

movement_dict = {
    "3.1운동": "AA", "3.1운동지원": "AB", "계몽운동": "AC",
    "광복군": "AE", "국내항일": "AG", "만주방면": "AJ",
    "의병": "AN", "의열투쟁": "AO", "임시정부": "AR", "학생운동": "AU"
}

selected_movement_name = st.selectbox("검색할 운동 계열을 선택해주세요:", list(movement_dict.keys()))
selected_code = movement_dict[selected_movement_name]

if st.button("1단계: 해당 계열 독립운동가 명단 검색"):
    with st.spinner('공공데이터 서버와 통신하고 있습니다...'):
        raw_xml, parsed_dict = fetch_activist_data(movement_code=selected_code)
        
        if parsed_dict and "error" not in parsed_dict:
            items = extract_items_safely(parsed_dict)
            
            if items:
                st.session_state['activists_list'] = items
                # 새로운 검색 시 하위 단계 데이터 초기화
                st.session_state['current_story_data'] = {}
                st.session_state['current_prompts'] = []
                st.success(f"총 {len(items)}명의 데이터를 찾았습니다. 아래에서 인물을 선택하세요.")
            else:
                st.error("XML 데이터 파싱 완료. 하지만 해당 계열에 등록된 인물 데이터가 없습니다.")
                st.session_state['activists_list'] = []
        else:
            st.error("공공데이터를 정상적으로 가져오지 못했습니다.")

# ==========================================
# 2단계: 웹툰 주인공 선택 및 스토리보드 생성
# ==========================================
if st.session_state['activists_list']:
    st.write("---")
    st.subheader("2. 웹툰의 주인공 선택 및 대본 생성")
    
    options = []
    for person in st.session_state['activists_list']:
        p_name = person.get('name', '이름불명')
        p_activity = person.get('activities', '내용없음')
        display_text = f"{p_name} - {str(p_activity)[:30]}..."
        options.append(display_text)
    
    selected_index = st.selectbox("인물 선택:", range(len(options)), format_func=lambda x: options[x])
    selected_person_data = st.session_state['activists_list'][selected_index]
    
    with st.expander("📌 선택한 인물 원본 데이터 보기"):
        st.json(selected_person_data)

    if st.button("2단계: 선택한 인물로 스토리보드 생성 시작"):
        if not gemini_key_input:
            st.warning("Gemini API 키를 먼저 입력해주세요.")
        else:
            with st.spinner('선택한 인물의 데이터로 대본을 창작하고 팩트체크 중입니다...'):
                story_data = generate_storyboard(gemini_api_key=gemini_key_input, parsed_data=selected_person_data)
                
                if story_data and "storyboard" in story_data:
                    st.success("스토리보드 생성이 완료되었습니다.")
                    st.session_state['current_story_data'] = story_data
                    st.session_state['current_prompts'] = [] # 스토리 변경 시 프롬프트 초기화
                else:
                    st.error("스토리보드 생성에 실패했거나 JSON 구조가 올바르지 않습니다.")

# 생성된 스토리 데이터 출력 (세션에 존재할 경우 항상 출력)
if st.session_state['current_story_data']:
    story_data = st.session_state['current_story_data']
    st.write("### 👤 캐릭터 외모 설정 (일관성 유지용)")
    st.info(story_data.get('character_appearance', '외모 정보 처리 누락'))
    
    st.write("### 📝 완성된 웹툰 스토리보드 (팩트체크 완료)")
    for cut in story_data['storyboard']:
        with st.expander(f"Cut {cut['cut']}"):
            st.markdown(f"**지문:** {cut['description']}")
            st.markdown(f"**대사:** {cut['dialogue']}")

# ==========================================
# 3단계: 이미지 생성 프롬프트 자동 작성
# ==========================================
if st.session_state['current_story_data']:
    st.write("---")
    st.subheader("3. 이미지 생성 프롬프트 자동 작성")
    
    if st.button("3단계: 스토리보드 기반 Animagine 프롬프트 생성"):
        if not gemini_key_input:
            st.warning("Gemini API 키를 먼저 입력해주세요.")
        else:
            with st.spinner('컷별 Danbooru 태그를 분석하고 생성 중입니다...'):
                story_data = st.session_state['current_story_data']
                prompts = generate_image_prompts(
                    gemini_api_key=gemini_key_input,
                    character_appearance=story_data['character_appearance'],
                    storyboard=story_data['storyboard']
                )
                
                if prompts:
                    st.success("프롬프트 생성이 완료되었습니다.")
                    st.session_state['current_prompts'] = prompts
                else:
                    st.error("프롬프트 생성에 실패했습니다.")

# 생성된 프롬프트 데이터 출력
if st.session_state['current_prompts']:
    prompts = st.session_state['current_prompts']
    for p in prompts:
        with st.container():
            st.markdown(f"**[Cut {p['cut']}]**")
            st.code(f"Positive: {p['positive_prompt']}\nNegative: {p['negative_prompt']}", language="text")

# ==========================================
# 4단계: ComfyUI 서버 구동 및 이미지 생성 (app.py 수정 부분)
# ==========================================
if st.session_state['current_prompts']:
    st.write("---")
    st.subheader("4. ComfyUI 연동 및 백그라운드 이미지 생성")
    
    # Git 설치 경로로 기본값 변경
    comfyui_absolute_path = st.text_input(
        "ComfyUI 폴더 절대 경로:", 
        value=r"C:/webtoon_agent/ComfyUI"
    )
    comfyui_server_url = st.text_input("ComfyUI 서버 주소:", value="http://127.0.0.1:8188")
    workflow_json_name = st.text_input("ComfyUI 워크플로우 파일명:", value="webtoon_randomseed.json")
    
    if st.button("4단계: 전체 컷 이미지 생성 대기열(Queue) 등록"):
        prompts = st.session_state['current_prompts']
        
        # 1. 서버 부팅 로직
        with st.spinner("ComfyUI 서버 상태를 확인하고 부팅합니다... (최대 1분 소요)"):
            is_server_ready = launch_comfyui_server(comfy_folder_path=comfyui_absolute_path, url=comfyui_server_url)
        
        if not is_server_ready:
            st.error("ComfyUI 서버 부팅 실패. 폴더 경로를 확인하시거나 수동으로 켜주세요.")
        else:
            st.success("서버 접속 완료. 대기열 전송을 시작합니다.")
            
            # 2. 이미지 생성 전송 로직
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            success_count = 0
            total_cuts = len(prompts)
            
            for idx, p in enumerate(prompts):
                status_text.text(f"Cut {p['cut']} 작업을 ComfyUI로 전송 중... ({idx+1}/{total_cuts})")
                
                is_success = queue_comfyui_prompt(
                    comfy_url=comfyui_server_url,
                    workflow_path=workflow_json_name,
                    positive_text=p['positive_prompt'],
                    negative_text=p['negative_prompt'],
                    cut_number=p['cut'], # <- 이 부분이 추가되어야 합니다.
                    batch_size=5
                )
                
                if is_success:
                    success_count += 1
                else:
                    st.error(f"Cut {p['cut']} 전송 실패. (서버 연결 또는 JSON 노드 ID 확인 필요)")
                    break
                    
                progress_bar.progress((idx + 1) / total_cuts)
                
            if success_count == total_cuts:
                status_text.text("모든 컷의 생성 요청이 완료되었습니다!")
                st.success("ComfyUI 백그라운드에서 이미지가 생성되고 있습니다. 다음 단계에서 이미지를 확인하세요.")
# ==========================================
# 7단계: 생성된 이미지 확인 및 최종 컷 선택
# ==========================================
if st.session_state['current_prompts']:
    st.write("---")
    st.subheader("7. 생성 이미지 확인 및 최종 컷 선택 (Human-in-the-Loop)")
    
    output_dir = os.path.join(comfyui_absolute_path, "output")
    final_dir = os.path.join(os.getcwd(), "final_webtoon") # 현재 프로젝트 폴더 아래에 생성
    
    if not os.path.exists(output_dir):
        st.warning(f"ComfyUI 출력 폴더({output_dir})를 찾을 수 없습니다. 아직 생성 전이거나 경로가 다릅니다.")
    else:
        if st.button("출력 폴더에서 생성된 이미지 불러오기"):
            st.session_state['image_selection_mode'] = True
            
    if st.session_state.get('image_selection_mode', False):
        st.success("이미지를 성공적으로 불러왔습니다. 각 컷마다 가장 마음에 드는 1장을 선택하세요.")
        
        selected_images_per_cut = {}
        
        # 컷별로 UI 생성
        for p in st.session_state['current_prompts']:
            cut_num = p['cut']
            prefix = f"cut_{cut_num}_"
            
            # 해당 컷의 접두사(prefix)를 가진 파일들만 수집
            cut_images = [f for f in os.listdir(output_dir) if f.startswith(prefix) and f.endswith(".png")]
            cut_images.sort() # 생성 순서대로 정렬
            
            with st.expander(f"🎬 Cut {cut_num} 이미지 선택 (후보 {len(cut_images)}장)", expanded=True):
                if not cut_images:
                    st.error(f"Cut {cut_num}에 해당하는 생성 이미지가 없습니다. ComfyUI 진행 상태를 확인하세요.")
                    continue
                
                # 라디오 버튼을 가로로 배치하기 위한 꼼수 (선택지 텍스트)
                options = [f"후보 {i+1}" for i in range(len(cut_images))]
                
                # 5개의 열을 만들어 이미지 나란히 배치
                cols = st.columns(len(cut_images))
                for i, img_file in enumerate(cut_images):
                    img_path = os.path.join(output_dir, img_file)
                    try:
                        img = Image.open(img_path)
                        cols[i].image(img, caption=f"후보 {i+1}", use_container_width=True)
                    except Exception as e:
                        cols[i].error("이미지 로드 실패")
                
                # 이미지 아래에 라디오 버튼 배치 (사용자가 1장 선택)
                selected_option = st.radio(f"Cut {cut_num} 최종 선택:", options, horizontal=True, key=f"radio_cut_{cut_num}")
                selected_idx = options.index(selected_option)
                
                # 선택된 파일명을 딕셔너리에 저장
                selected_images_per_cut[cut_num] = os.path.join(output_dir, cut_images[selected_idx])
        
        # ==========================================
        # 최종 웹툰 폴더로 복사 및 대사/지문 미리보기
        # ==========================================
        st.write("---")
        if st.button("✅ 선택한 이미지 최종 웹툰 폴더로 저장하기"):
            os.makedirs(final_dir, exist_ok=True)
            
            success_copy = 0
            for cut_num, source_path in selected_images_per_cut.items():
                target_path = os.path.join(final_dir, f"최종_cut_{cut_num}.png")
                try:
                    shutil.copy2(source_path, target_path)
                    success_copy += 1
                except Exception as e:
                    st.error(f"Cut {cut_num} 저장 실패: {e}")
                    
            if success_copy == len(selected_images_per_cut):
                st.success(f"총 {success_copy}장의 최종 이미지가 '{final_dir}' 폴더에 안전하게 저장되었습니다.")
                
                # --- 여기서부터 추가된 미리보기 UI 로직 ---
                st.write("---")
                st.subheader("📺 최종 웹툰 결과물 미리보기")
                
                # 세션에서 대본 데이터 가져오기
                storyboard_data = st.session_state['current_story_data'].get('storyboard', [])
                
                # 컷 번호 순서대로 정렬하여 출력
                for cut_num in sorted(selected_images_per_cut.keys()):
                    # 해당 컷 번호와 일치하는 대본 찾기
                    cut_text = next((item for item in storyboard_data if item["cut"] == cut_num), None)
                    
                    st.write(f"### 🎬 Cut {cut_num}")
                    
                    # 1. 최종 선택된 이미지 화면에 출력
                    final_img_path = os.path.join(final_dir, f"최종_cut_{cut_num}.png")
                    try:
                        st.image(final_img_path, use_container_width=True)
                    except Exception as e:
                        st.error(f"이미지 출력 오류: {e}")
                    
                    # 2. 매칭된 지문(자막)과 대사 출력
                    if cut_text:
                        st.info(f"**[지문/자막]** {cut_text['description']}")
                        st.warning(f"**[대사]** {cut_text['dialogue']}")
                    else:
                        st.error("해당 컷의 대본 데이터를 찾을 수 없습니다.")