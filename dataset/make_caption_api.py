import json
import os
import glob
from openai import OpenAI
from dotenv import load_dotenv

# ==========================================
# 사용자 설정 영역
# ==========================================
# 1. 여기에 발급받은 OpenAI API 키를 입력하세요.
# OPENAI_API_KEY = "YOUR_API_KEY_HERE"

# 2. JSON 및 이미지 파일들이 모여있는 폴더 경로 (현재 폴더면 '.')
TARGET_FOLDER = 'dataset/image_json' 

# 3. 학습할 화풍을 호출할 나만의 고유 단어 (예: bgbd_style)
TRIGGER_WORD = 'webtoon_style' 
# ==========================================

load_dotenv()
client = OpenAI()

def generate_flux_prompt(korean_data):
    """GPT-4o-mini를 사용하여 FLUX 최적화 프롬프트 생성"""
    system_prompt = """
    You are an expert prompt engineer for FLUX image generation models.
    Your task is to translate and convert Korean image metadata into a single, cohesive, natural English sentence.
    
    CRITICAL RULES:
    1. DO NOT include any words related to art style, medium, or format (e.g., webtoon, manga, anime, illustration, drawing, painting, cel shading).
    2. Focus ONLY on objective visual elements: subject, pose, expression, clothing, lighting, camera angle, and background.
    3. Translate Korean specific terms accurately into natural anatomical/visual English (e.g., "실눈" -> "narrow eyes", "살구색" -> "peach skin", "각진형" -> "angular face").
    4. Provide ONLY the translated English sentence, without any introductory or concluding remarks.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this data into a FLUX prompt: {korean_data}"}
            ],
            temperature=0.2 
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API 통신 에러: {e}")
        return None

def check_image_exists(json_path, folder_path):
    """JSON 파일명에 대응하는 이미지 파일이 존재하는지 검사"""
    base_name = os.path.basename(json_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    # AI Hub 데이터셋 규칙 (L -> S 변환, 예: LR089121 -> SR089121)
    if name_without_ext.startswith('L'):
        img_base_name = 'S' + name_without_ext[1:]
    else:
        img_base_name = name_without_ext
        
    # 흔히 사용되는 이미지 확장자 교차 검색
    valid_extensions = ['.jpg', '.jpeg', '.png', '.JPEG', '.PNG']
    
    for ext in valid_extensions:
        if os.path.exists(os.path.join(folder_path, img_base_name + ext)):
            return True, img_base_name + ext
            
    return False, None

def process_dataset(folder_path, trigger_word):
    json_files = glob.glob(os.path.join(folder_path, '*.json'))
    success_count = 0
    skip_count = 0
    
    print(f"총 {len(json_files)}개의 JSON 파일을 스캔합니다...\n")
    
    for json_path in json_files:
        try:
            # 1. 짝꿍 이미지 파일 존재 여부 선행 검사
            img_exists, img_name = check_image_exists(json_path, folder_path)
            
            if not img_exists:
                print(f"[스킵] {os.path.basename(json_path)} - 대응하는 이미지 파일이 없어 API 번역을 건너뜁니다.")
                skip_count += 1
                continue # 다음 파일로 넘어감
                
            # 2. 이미지가 존재할 경우에만 JSON 읽기 및 API 호출 진행
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            label = data.get('label', {})
            composition = label.get('directing', {}).get('composition', {})
            
            shot = composition.get('shot', '')
            angle = composition.get('angle', '')
            lighting = composition.get('lighting', '')
            caption = data.get('caption', '')
            
            char_info = ""
            chars = label.get('character', {}).get('char_info', [])
            if chars:
                char_info = chars[0].get('shape', '')
            
            korean_context = f"카메라/조명: {shot}, {angle}, {lighting} | 인물외형: {char_info} | 상황묘사: {caption}"
            
            # API 번역 요청 (이 단계에서만 과금 발생)
            english_translation = generate_flux_prompt(korean_context)
            
            if english_translation:
                final_prompt = f"{trigger_word}, {english_translation}"
                
                txt_path = json_path.replace('.json', '.txt')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(final_prompt)
                    
                success_count += 1
                print(f"[완료] {os.path.basename(txt_path)} 생성됨 (확인된 이미지: {img_name})")
            else:
                print(f"[실패] {os.path.basename(json_path)} - API 응답 없음")
                
        except Exception as e:
            print(f"[오류] {os.path.basename(json_path)} 처리 중 문제 발생: {e}")

    print(f"\n==========================================")
    print(f"작업 완료 요약:")
    print(f"- 생성 성공: {success_count} 개")
    print(f"- 누락 스킵: {skip_count} 개")
    print(f"==========================================")

if __name__ == "__main__":
    process_dataset(TARGET_FOLDER, TRIGGER_WORD)