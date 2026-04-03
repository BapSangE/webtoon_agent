import streamlit as st
import os
import shutil
import json
import requests
from PIL import Image
from database import SessionLocal, Activist, WebtoonProject
from generatestory import generate_storyboard
from generateprompts import generate_image_prompts
from generateimages import queue_comfyui_prompt,queue_inpaint_prompt
from start_server import launch_comfyui_server
import io
import zipfile
import csv

def create_canva_export_zip(storyboard_json, image_paths_dict):
    """
    storyboard_json: LLM이 생성한 스토리보드 리스트 (예: [{"cut":1, "dialogue":"..."}, ...])
    image_paths_dict: 생성된 이미지의 물리적 경로 딕셔너리 (예: {1: "./output/cut1.png", 2: ...})
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Canva 대량 제작용 CSV 데이터 생성 (메모리)
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer)
        csv_writer.writerow(["Cut", "Image_File", "Description", "Narration", "Dialogue"])

        for item in storyboard_json:
            cut_num = item.get("cut")
            desc = item.get("description", "")
            narr = item.get("narration", "")
            dial = item.get("dialogue", "")
            
            img_path = image_paths_dict.get(cut_num)
            img_filename = f"cut_{cut_num}.png" if img_path else ""

            # CSV 행 기록
            csv_writer.writerow([cut_num, img_filename, desc, narr, dial])

            # 2. 물리적 이미지 파일을 ZIP에 추가
            if img_path:
                try:
                    zip_file.write(img_path, arcname=img_filename)
                except FileNotFoundError:
                    pass

        # 3. 완성된 CSV를 ZIP에 추가 (한글 깨짐 방지를 위해 utf-8-sig 사용)
        zip_file.writestr("canva_webtoon_script.csv", csv_buffer.getvalue().encode('utf-8-sig'))

    return zip_buffer.getvalue()

    # ComtyUI Path,URL
comfyui_path = st.text_input("ComfyUI 폴더 절대 경로 확인 :", value=r"C:/comfyuipj/ComfyUI")
comfyui_url = st.text_input("ComfyUI 서버 주소 확인:", value="http://127.0.0.1:8188")

# ComfyUI 생성 강제 중단 함수
def stop_comfyui_generation(comfy_url: str):
    try:
        # 1. 큐(대기열) 전체 비우기
        requests.post(f"{comfy_url}/queue", json={"clear": True}, timeout=2)
        # 2. 현재 진행 중인 연산 물리적 강제 중단
        requests.post(f"{comfy_url}/interrupt", timeout=2)
        return True
    except Exception as e:
        return False

# ==========================================
# 화면 기본 설정 및 UI 스타일 주입
# ==========================================
st.set_page_config(page_title="독립운동가 웹툰 에이전트", page_icon="📜", layout="centered")

def apply_custom_ui():
    st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    div.stButton > button {
        background-color: #0ea5e9; color: #ffffff !important; border-radius: 8px;
        border: none; padding: 0.5rem 1rem; font-weight: 600; width: 100%;
    }
    div[data-testid="stExpander"], div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(10px);
        border: 1px solid #e2e8f0; border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_ui()

# ==========================================
# 스크롤 가능한 원본 이미지 팝업 함수
# ==========================================
@st.dialog("🔍 원본 크기 보기 (상하 스크롤 가능)", width="large")
def show_large_image(img_path):
    img = Image.open(img_path)
    st.image(img, use_container_width=True)

# 세션 상태 초기화
if 'activists_list' not in st.session_state: st.session_state['activists_list'] = []
if 'current_story_data' not in st.session_state: st.session_state['current_story_data'] = {}
if 'current_prompts' not in st.session_state: st.session_state['current_prompts'] = []
if 'parsed_data' not in st.session_state: st.session_state['parsed_data'] = {}

st.title("📜 독립운동가 웹툰 제작 에이전트")
gemini_key_input = st.text_input("Gemini API 키를 입력하세요:", type="password")

# ==========================================
# 사이드바: 0단계(히스토리) 및 1단계(인물 검색)
# ==========================================
db = SessionLocal()

with st.sidebar:
    st.header("📂 0. 이전 작업 불러오기")
    try:
        past_projects = db.query(WebtoonProject, Activist).join(Activist).order_by(WebtoonProject.created_at.desc()).all()
        if past_projects:
            project_options = ["새로 시작하기"] + [
                f"[{p.WebtoonProject.project_id}] {p.Activist.name_ko} ({p.WebtoonProject.created_at.strftime('%m-%d %H:%M')})" 
                for p in past_projects
            ]
            selected_project_str = st.selectbox("저장된 프로젝트 선택", project_options)
            
            if selected_project_str != "새로 시작하기":
                proj_id = int(selected_project_str.split("]")[0].replace("[", ""))
                
                # [수정됨] 복원 버튼과 삭제 버튼을 나란히 배치하기 위해 컬럼 분할
                btn_cols = st.columns(2)
                
                # 1. 복원 버튼 로직
                with btn_cols[0]:
                    if st.button("📂 복원하기", use_container_width=True):
                        target_proj = db.query(WebtoonProject).filter(WebtoonProject.project_id == proj_id).first()
                        target_activist = db.query(Activist).filter(Activist.id == target_proj.activist_id).first()
                        
                        st.session_state['current_project_id'] = target_proj.project_id
                        st.session_state['parsed_data'] = {
                            "name": target_activist.name_ko,
                            "content": target_activist.content,
                            "activities": target_activist.activities,
                            "born_died": target_activist.born_died,
                            "engaged_organizations": target_activist.engaged_organizations
                        }
                        st.session_state['current_story_data'] = {
                            "character_appearance": target_proj.character_appearance,
                            "storyboard": target_proj.storyboard_json
                        }
                        st.session_state['current_prompts'] = target_proj.prompts_json if target_proj.prompts_json else []
                        st.success(f"{target_activist.name_ko} 지사님 데이터 복원 완료")
                
                # 2. 삭제 버튼 로직
                with btn_cols[1]:
                    if st.button("🗑️ 삭제하기", use_container_width=True):
                        target_proj = db.query(WebtoonProject).filter(WebtoonProject.project_id == proj_id).first()
                        if target_proj:
                            db.delete(target_proj)
                            db.commit()
                            st.rerun() # 삭제 완료 후 즉시 화면을 새로고침하여 목록 갱신
        else:
            st.info("저장된 프로젝트가 없습니다.")
    except Exception as e:
        st.error(f"히스토리 로드 에러: {e}")

    st.markdown("---")
    st.header("1. 독립운동가 검색")
    movement_type = st.selectbox("운동 계열 선택", ["3.1운동", "계몽운동", "광복군", "국내항일", "의병", "의열투쟁", "임시정부"])
    activists = db.query(Activist).filter(Activist.movement_type == movement_type).order_by(Activist.name_ko.asc()).all()
    if activists:
        activist_names = [f"{a.name_ko} ({a.born_died})" for a in activists]
        selected_name_full = st.selectbox("인물 선택", activist_names)
        selected_name = selected_name_full.split(" (")[0]
        current_activist = next(a for a in activists if a.name_ko == selected_name)
        
        if st.button("데이터 확정 및 분석 시작"):
            st.session_state['parsed_data'] = {
                "name": current_activist.name_ko,
                "content": current_activist.content,
                "activities": current_activist.activities,
                "born_died": current_activist.born_died,
                "engaged_organizations": current_activist.engaged_organizations
            }
            st.success(f"{current_activist.name_ko} 지사 데이터 로드 완료")
    # 사이드바 하단 - 시스템 제어 영역
    st.markdown("---")
    st.subheader("⚙️ 시스템 제어")
    
    st.warning("이미지 생성이 너무 오래 걸리거나 잘못된 요청이 들어간 경우 아래 버튼을 누르세요.")
    if st.button("🛑 진행 중인 생성 강제 중단", use_container_width=True, type="primary"):
        is_stopped = stop_comfyui_generation(comfyui_url)
        if is_stopped:
            st.success("✅ ComfyUI 연산 및 대기열이 완전히 중단되었습니다.")
        else:
            st.error("❌ 중단 요청 실패. 서버 연결을 확인하세요.")

db.close()

# ==========================================
# 2~3단계: 스토리 및 프롬프트 생성 (DB 저장 + 화면 출력)
# ==========================================
if st.session_state.get('parsed_data'):
    st.write("---")
    st.subheader("2. 웹툰 스토리보드 생성")
    if st.button("2단계: 스토리보드 생성 시작"):
        if not gemini_key_input: 
            st.warning("API 키를 입력하세요.")
        else:
            with st.spinner('스토리 생성 중...'):
                story_data = generate_storyboard(gemini_api_key=gemini_key_input, parsed_data=st.session_state['parsed_data'])
                if story_data:
                    st.session_state['current_story_data'] = story_data
                    
                    # DB 저장 로직 (INSERT)
                    db = SessionLocal()
                    try:
                        activist = db.query(Activist).filter(Activist.name_ko == st.session_state['parsed_data']['name']).first()
                        if activist:
                            new_project = WebtoonProject(
                                activist_id=activist.id,
                                character_appearance=story_data['character_appearance'],
                                storyboard_json=story_data['storyboard']
                            )
                            db.add(new_project)
                            db.commit()
                            db.refresh(new_project)
                            st.session_state['current_project_id'] = new_project.project_id
                    except Exception as e:
                        st.error(f"DB 저장 오류: {e}")
                    finally:
                        db.close()
                        
                    st.success("스토리보드 생성 및 DB 저장 완료")

    # [복구됨] 2단계 데이터 화면 출력 UI
    if st.session_state.get('current_story_data'):
        st.markdown("#### 👤 캐릭터 외모 설정")
        st.info(st.session_state['current_story_data']['character_appearance'])
        
        st.markdown("#### 📖 컷별 스토리보드")
        for cut in st.session_state['current_story_data']['storyboard']:
            bg_text = cut.get('visual_elements', {}).get('background', '배경 미지정')
            time_text = cut.get('visual_elements', {}).get('time_of_day', '시간 미지정') # 기존에 time_of_day가 없다면 제외 가능
            
            desc_text = cut.get('description', '')
            narra_text = cut.get('narration', '') # [추가됨] 자막 데이터 로드
            dial_text = cut.get('dialogue', '')
            
            # visual_elements가 통째로 딕셔너리로 들어오므로 문자열로 변환하여 출력
            vis_text = str(cut.get('visual_elements', '')) 
            
            with st.expander(f"🎬 Cut {cut.get('cut', '?')} : {bg_text}"):
                st.write(f"**지문:** {desc_text}")
                st.write(f"**자막(내레이션):** {narra_text}") # [추가됨] 화면에 자막 출력
                st.write(f"**대사:** {dial_text}")
                st.write(f"**시각 요소:** {vis_text}")


if st.session_state.get('current_story_data'):
    st.write("---")
    st.subheader("3. 이미지 생성 프롬프트 자동 작성")
    if st.button("3단계: 프롬프트 태그 생성"):
        with st.spinner('태그 분석 중...'):
            prompts = generate_image_prompts(
                gemini_api_key=gemini_key_input,
                character_appearance=st.session_state['current_story_data']['character_appearance'],
                storyboard=st.session_state['current_story_data']['storyboard']
            )
            if prompts:
                st.session_state['current_prompts'] = prompts
                
                # DB 업데이트 로직 (UPDATE)
                if 'current_project_id' in st.session_state:
                    db = SessionLocal()
                    try:
                        project = db.query(WebtoonProject).filter(WebtoonProject.project_id == st.session_state['current_project_id']).first()
                        if project:
                            project.prompts_json = prompts
                            db.commit()
                    except Exception as e:
                        st.error(f"프롬프트 DB 업데이트 오류: {e}")
                    finally:
                        db.close()
                        
                st.success("프롬프트 생성 및 DB 업데이트 완료")

    # [복구됨] 3단계 프롬프트 화면 출력 UI
    if st.session_state.get('current_prompts'):
        st.markdown("#### 📝 컷별 생성 프롬프트")
        for p in st.session_state['current_prompts']:
            with st.expander(f"⚙️ Cut {p['cut']} 프롬프트"):
                st.markdown("**Positive Prompt:**")
                st.code(p['positive_prompt'], language='text')
                st.markdown("**Negative Prompt:**")
                st.code(p['negative_prompt'], language='text')

# ==========================================
# 4단계: ComfyUI 연동 및 자동화 생성 (수정본)
# ==========================================
if st.session_state.get('current_prompts'):
    st.write("---")
    st.subheader("4. ComfyUI 연동 및 백그라운드 이미지 생성")

    st.info("💡 시스템이 프롬프트를 분석하여 '일반' 혹은 '국기 합성(SAM)' 워크플로우를 자동 선택합니다.")
    
    if st.button("4단계: 전체 컷 생성 대기열 등록"):
        with st.spinner("서버 부팅 확인 중..."):
            if launch_comfyui_server(comfy_folder_path=comfyui_path, url=comfyui_url):
                progress_bar = st.progress(0)
                success_count = 0
                total = len(st.session_state['current_prompts'])
                activist_name = st.session_state['parsed_data']['name']
                
                for idx, p in enumerate(st.session_state['current_prompts']):
                    # 수정됨: workflow_path 제거, activist_name 추가
                    is_success = queue_comfyui_prompt(
                        comfy_url=comfyui_url,
                        positive_text=p['positive_prompt'],
                        negative_text=p['negative_prompt'],
                        cut_number=p['cut'],
                        activist_name=activist_name,
                        batch_size=5
                    )
                    if is_success: success_count += 1
                    progress_bar.progress((idx + 1) / total)
                
                if success_count == total: st.success(f"모든 컷 전송 완료 (폴더: output/{activist_name})")

# ==========================================
# 7단계: 인물별 폴더 기반 이미지 확인 및 선택 (수정본)
# ==========================================
if st.session_state.get('current_prompts'):
    st.write("---")
    st.subheader("7. 생성 이미지 확인 및 최종 컷 선택")
    
    activist_name = st.session_state['parsed_data']['name']
    safe_name = activist_name.replace(" ", "_")
    output_dir = os.path.join(comfyui_path, "output", safe_name)
    final_dir = os.path.join(os.getcwd(), f"final_webtoon_{safe_name}")
    
    if st.button("인물 전용 폴더에서 이미지 불러오기"):
        if os.path.exists(output_dir):
            st.session_state['image_selection_mode'] = True
        else:
            st.error(f"폴더를 찾을 수 없습니다: {output_dir}")

    if st.session_state.get('image_selection_mode'):
        selected_images = {}
        storyboard = st.session_state['current_story_data'].get('storyboard', [])
        
        for p in st.session_state['current_prompts']:
            cut_num = p['cut']
            cut_images = [f for f in os.listdir(output_dir) if f.startswith(f"cut_{cut_num}_") and f.endswith(".png")]
            cut_images.sort()
            
            with st.expander(f"🎬 Cut {cut_num} (후보 {len(cut_images)}장)", expanded=True):
                cut_text = next((item for item in storyboard if item["cut"] == cut_num), None)
                if cut_text:
                    desc_text = cut_text.get('description', '')
                    narra_text = cut_text.get('narration', '')
                    dial_text = cut_text.get('dialogue', '')
                    st.info(f"**지문:** {desc_text} \n\n **자막:** {narra_text} \n\n **대사:** {dial_text}")
                
                # 1. 인페인팅(태극기 합성) 완료 파일 스캔 및 최상단 표시
                inpaint_files = [f for f in os.listdir(output_dir) if f.startswith(f"inpaint_cut_{cut_num}_") and f.endswith(".png")]
                
                if inpaint_files:
                    # 가장 최근에 만들어진 합성본 1장만 추출
                    inpaint_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
                    latest_inpaint_path = os.path.join(output_dir, inpaint_files[0])
                    
                    st.success("✅ 🇰🇷 가장 최근에 합성된 태극기 이미지입니다. (마음에 들지 않으면 아래에서 다른 원본을 골라 다시 합성하세요)")
                    st.image(Image.open(latest_inpaint_path), caption=f"Cut {cut_num} 최종 합성본", use_container_width=True)
                    
                    # 최종 저장 경로를 우선적으로 합성본으로 세팅
                    selected_images[cut_num] = latest_inpaint_path
                    st.markdown("---")
                
                # 2. 원본 후보 선택 UI
                if cut_images:
                    st.markdown("#### 🖼️ 원본 후보 선택 (재합성용)")
                    st.info("💡 팁: [🔍 확대] 버튼을 누르면 위아래가 잘리지 않고 스크롤 가능한 큰 창이 열립니다.")
                    
                    cols = st.columns(len(cut_images))
                    for i, img_file in enumerate(cut_images):
                        img_path = os.path.join(output_dir, img_file)
                        with cols[i]:
                            # 이미지 렌더링
                            img = Image.open(img_path)
                            st.image(img, caption=f"후보 {i+1}", use_container_width=True)
                            
                            # [수정됨] 확대 버튼과 삭제 버튼을 나란히 배치하기 위한 하위 컬럼 분할
                            btn_cols = st.columns(2)
                            with btn_cols[0]:
                                if st.button("🔍 확대", key=f"zoom_{cut_num}_{img_file}"):
                                    show_large_image(img_path) # 최상단에 정의한 팝업 함수 호출
                            with btn_cols[1]:
                                if st.button("🗑️ 삭제", key=f"del_{cut_num}_{img_file}"):
                                    try:
                                        os.remove(img_path)
                                        st.rerun() # 삭제 후 즉시 화면 새로고침
                                    except Exception as e:
                                        st.error(f"삭제 실패: {e}")
                    
                    # 삭제 후 남아있는 이미지들을 기준으로 라디오 버튼 렌더링
                    sel = st.radio(f"Cut {cut_num} 원본 선택:", [f"후보 {i+1}" for i in range(len(cut_images))], horizontal=True, key=f"r_{cut_num}")
                    
                    selected_idx = int(sel.split()[-1]) - 1
                    selected_image_path = os.path.join(output_dir, cut_images[selected_idx])
                    
                    # 만약 합성 파일이 단 하나도 없다면, 여기서 고른 원본을 최종 저장 경로로 세팅
                    if not inpaint_files:
                        selected_images[cut_num] = selected_image_path
                    
                    # 🔄 이 컷만 5장 다시 생성 버튼
                    st.write("") 
                    if st.button(f"🔄 Cut {cut_num} 후보 5장 추가 생성", key=f"re_gen_{cut_num}"):
                        with st.spinner(f"Cut {cut_num}의 새로운 후보 5장을 요청 중..."):
                            is_success = queue_comfyui_prompt(
                                comfy_url=comfyui_url,
                                positive_text=p['positive_prompt'],
                                negative_text=p['negative_prompt'],
                                cut_number=cut_num,
                                activist_name=activist_name,
                                batch_size=5
                            )
                            if is_success:
                                st.success("ComfyUI 대기열에 추가되었습니다. 잠시 후 이미지가 생성되면 화면에 나타납니다.")
                                st.rerun()
                        
                    # 3. 태극기 합성 버튼 항상 표시
                    prompt_lower = p['positive_prompt'].lower()
                    if "flag" in prompt_lower or "taegeukgi" in prompt_lower:
                        st.warning("위에서 다른 원본을 고른 뒤 버튼을 누르면 태극기를 다시 합성합니다.")
                        if st.button(f"🇰🇷 Cut {cut_num} 태극기 자동 합성 (재실행 가능)", key=f"btn_inpaint_{cut_num}"):
                            with st.spinner("ComfyUI에서 태극기를 다시 합성 중입니다... (약 10초 소요)"):
                                is_success = queue_inpaint_prompt(
                                    comfy_url=comfyui_url,
                                    comfyui_path=comfyui_path,
                                    source_image_path=selected_image_path,
                                    positive_text=p['positive_prompt'],
                                    negative_text=p['negative_prompt'],
                                    cut_number=cut_num,
                                    activist_name=activist_name
                                )
                                if is_success:
                                    # 합성 성공 시 즉시 새로고침하여 바뀐 이미지를 최상단에 로드
                                    st.rerun() 
                                else:
                                    st.error("합성 실패. ComfyUI 로그를 확인하세요.")
        # ==========================================
        # 8단계: Canva 연동을 위한 최종 ZIP 추출 (여기에 붙여넣기!)
        # ==========================================
        st.markdown("---")
        st.subheader("8. 최종 데이터 Canva 추출")
        st.info("선택된 이미지와 대사본(CSV)을 한 번에 다운로드하여 Canva '대량 제작' 기능에 활용하세요.")
        
        # 선택된 이미지가 하나라도 있는지 확인
        if selected_images:
            try:
                zip_data = create_canva_export_zip(storyboard, selected_images)
                st.download_button(
                    label="📦 이미지 + 대사본 ZIP 다운로드",
                    data=zip_data,
                    file_name=f"{safe_name}_canva_export.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"ZIP 압축 중 오류 발생: {e}")
        else:
            st.warning("아직 생성되거나 선택된 이미지가 없습니다.")