# generateimages.py
import json
import requests
import copy
import random # 난수 생성을 위한 라이브러리 추가

def queue_comfyui_prompt(comfy_url: str, workflow_path: str, positive_text: str, negative_text: str, batch_size: int = 5) -> bool:
    """
    제공된 JSON 구조에 맞춰 랜덤 시드와 프롬프트를 주입하고 ComfyUI 대기열에 등록합니다.
    """
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
            
        prompt_payload = copy.deepcopy(workflow_data)
        
        # 제공해주신 webtoon.json 구조에 맞춘 정확한 노드 ID 매핑
        KSAMPLER_NODE_ID = "5"
        POSITIVE_NODE_ID = "6"
        LATENT_NODE_ID = "7"
        NEGATIVE_NODE_ID = "8"
        
        # 1. 텍스트 및 배치 사이즈 주입
        prompt_payload[POSITIVE_NODE_ID]["inputs"]["text"] = positive_text
        prompt_payload[NEGATIVE_NODE_ID]["inputs"]["text"] = negative_text
        prompt_payload[LATENT_NODE_ID]["inputs"]["batch_size"] = batch_size
        
        # 2. 랜덤 시드 생성 및 주입 (화풍 유지, 구도 다양화)
        random_seed = random.randint(1, 1000000000000000)
        prompt_payload[KSAMPLER_NODE_ID]["inputs"]["seed"] = random_seed
        
        api_endpoint = f"{comfy_url.rstrip('/')}/prompt"
        data = {"prompt": prompt_payload}
        
        response = requests.post(api_endpoint, json=data)
        
        if response.status_code == 200:
            return True
        else:
            print(f"ComfyUI 오류 반환: {response.status_code} - {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"오류: {workflow_path} 파일을 찾을 수 없습니다.")
        return False
    except requests.exceptions.ConnectionError:
        print(f"오류: ComfyUI 서버({comfy_url})에 연결할 수 없습니다. 서버가 켜져 있는지 확인하세요.")
        return False
    except Exception as e:
        print(f"이미지 생성 요청 중 알 수 없는 오류 발생: {e}")
        return False