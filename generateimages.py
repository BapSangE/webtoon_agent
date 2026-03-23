# generateimages.py
import json
import requests
import copy
import random

def queue_comfyui_prompt(comfy_url: str, workflow_path: str, positive_text: str, negative_text: str, cut_number: int, batch_size: int = 5) -> bool:
    """
    [수정됨] cut_number를 추가로 입력받아 이미지 파일명(prefix)을 컷별로 분리합니다.
    """
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
            
        prompt_payload = copy.deepcopy(workflow_data)
        
        KSAMPLER_NODE_ID = "5"
        POSITIVE_NODE_ID = "6"
        LATENT_NODE_ID = "7"
        NEGATIVE_NODE_ID = "8"
        SAVE_NODE_ID = "10" # 추가: 이미지 저장 노드
        
        prompt_payload[POSITIVE_NODE_ID]["inputs"]["text"] = positive_text
        prompt_payload[NEGATIVE_NODE_ID]["inputs"]["text"] = negative_text
        prompt_payload[LATENT_NODE_ID]["inputs"]["batch_size"] = batch_size
        
        random_seed = random.randint(1, 1000000000000000)
        prompt_payload[KSAMPLER_NODE_ID]["inputs"]["seed"] = random_seed
        
        # 추가: 파일명을 cut_1, cut_2 등으로 지정
        prompt_payload[SAVE_NODE_ID]["inputs"]["filename_prefix"] = f"cut_{cut_number}"
        
        api_endpoint = f"{comfy_url.rstrip('/')}/prompt"
        data = {"prompt": prompt_payload}
        
        response = requests.post(api_endpoint, json=data)
        
        if response.status_code == 200:
            return True
        else:
            print(f"ComfyUI 오류 반환: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"이미지 생성 요청 중 오류 발생: {e}")
        return False