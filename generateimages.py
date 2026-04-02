import json
import requests
import copy
import random
import traceback
import os
import shutil

def queue_comfyui_prompt(comfy_url: str, positive_text: str, negative_text: str, cut_number: int, activist_name: str, batch_size: int = 5) -> bool:
    # 1. 이제 무조건 일반 워크플로우(workflow_normal.json)만 사용합니다.
    workflow_path = "workflow_normal.json"
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            prompt_payload = json.load(f)
    except FileNotFoundError:
        print(f"[중단] {workflow_path} 파일을 찾을 수 없습니다.")
        return False

    # 2. 일반 워크플로우의 노드 ID (자신의 JSON 번호와 일치하는지 확인 필수)
    POSITIVE_NODE_ID = "6"
    NEGATIVE_NODE_ID = "8"
    KSAMPLER_NODE_ID = "5"
    LATENT_NODE_ID = "7"
    SAVE_NODE_ID = "15"

    # 3. 페이로드 데이터 조작
    try:
        prompt_payload[POSITIVE_NODE_ID]["inputs"]["text"] = positive_text
        prompt_payload[NEGATIVE_NODE_ID]["inputs"]["text"] = negative_text
        
        random_seed = random.randint(1, 1000000000000000)
        prompt_payload[KSAMPLER_NODE_ID]["inputs"]["seed"] = random_seed
        prompt_payload[LATENT_NODE_ID]["inputs"]["batch_size"] = batch_size
        
        # 폴더 분리 및 파일명 지정
        safe_name = activist_name.replace(" ", "_")
        prompt_payload[SAVE_NODE_ID]["inputs"]["filename_prefix"] = f"{safe_name}/cut_{cut_number}"

        # ========================================================
        # [성별 기반 한복 LoRA 자동 스위칭 로직 (유지)]
        # ========================================================
        FEMALE_LORA_ID = "17"
        MALE_LORA_ID = "18"
        
        prompt_lower = positive_text.lower()
        
        if "1girl" in prompt_lower or "woman" in prompt_lower or "female" in prompt_lower:
            prompt_payload[FEMALE_LORA_ID]["inputs"]["strength_model"] = 0.7
            prompt_payload[MALE_LORA_ID]["inputs"]["strength_model"] = 0.0
        elif "1boy" in prompt_lower or "man" in prompt_lower or "male" in prompt_lower:
            prompt_payload[MALE_LORA_ID]["inputs"]["strength_model"] = 0.7
            prompt_payload[FEMALE_LORA_ID]["inputs"]["strength_model"] = 0.0
        # ========================================================

    except KeyError as ke:
        print(f"[중단] JSON 파일 내부에서 노드 ID {ke}를 찾을 수 없습니다.")
        return False

    # 4. API 전송
    api_endpoint = f"{comfy_url.rstrip('/')}/prompt"
    
    try:
        response = requests.post(api_endpoint, json={"prompt": prompt_payload}, timeout=60)
        if response.status_code == 200:
            print(f"[성공] Cut {cut_number} (일반) 렌더링 요청 완료")
            return True
        else:
            print(f"[서버 거부] ComfyUI 에러 반환: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[통신 에러] ComfyUI 서버에 연결할 수 없습니다: {e}")
        return False
    
def queue_inpaint_prompt(comfy_url: str, comfyui_path: str, source_image_path: str, positive_text: str, negative_text: str, cut_number: int, activist_name: str) -> bool:
    workflow_path = "workflow_inpaint_only.json"

    # 1. 스트림릿에서 고른 이미지를 ComfyUI의 input 폴더로 복사
    input_dir = os.path.join(comfyui_path, "input")
    os.makedirs(input_dir, exist_ok=True)
    target_filename = f"inpaint_target_cut_{cut_number}.png"
    target_image_path = os.path.join(input_dir, target_filename)
    shutil.copy2(source_image_path, target_image_path)

    try:
        # 2. 인페인트 전용 JSON 로드
        with open(workflow_path, 'r', encoding='utf-8') as f:
            prompt_payload = json.load(f)

        # 3. 노드 ID 세팅 (※ 본인의 워크플로우 화면에 맞춰 번호 확인 필수!)
        LOAD_IMAGE_NODE_ID = "39" # [수정 필수] 새로 꺼낸 Load Image 노드의 번호
        KSAMPLER_NODE_ID = "37"   # 남아있는 2차 KSampler 번호
        POSITIVE_NODE_ID = "6"
        NEGATIVE_NODE_ID = "8"
        SAVE_NODE_ID = "15"

        # 4. 페이로드 데이터 조작
        prompt_payload[LOAD_IMAGE_NODE_ID]["inputs"]["image"] = target_filename
        prompt_payload[POSITIVE_NODE_ID]["inputs"]["text"] = positive_text
        prompt_payload[NEGATIVE_NODE_ID]["inputs"]["text"] = negative_text
        
        random_seed = random.randint(1, 1000000000000000)
        prompt_payload[KSAMPLER_NODE_ID]["inputs"]["seed"] = random_seed
        
        safe_name = activist_name.replace(" ", "_")
        prompt_payload[SAVE_NODE_ID]["inputs"]["filename_prefix"] = f"{safe_name}/inpaint_cut_{cut_number}"

        # 5. API 전송
        api_endpoint = f"{comfy_url.rstrip('/')}/prompt"
        response = requests.post(api_endpoint, json={"prompt": prompt_payload}, timeout=60)
        
        if response.status_code == 200:
            print(f"[성공] Cut {cut_number} 인페인팅 렌더링 요청 완료")
            return True
        else:
            print(f"[서버 거부] ComfyUI 에러 반환: {response.text}")
            return False

    except Exception as e:
        print(f"[에러] 인페인팅 요청 실패: {e}")
        return False