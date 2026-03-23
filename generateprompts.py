# generateprompts.py
from google import genai
from google.genai import types
import json

def generate_image_prompts(gemini_api_key: str, character_appearance: str, storyboard: list) -> list:
    """
    스토리보드와 외모 설정을 바탕으로 Animagine XL 4.0 전용 프롬프트를 생성합니다.
    """
    client = genai.Client(api_key=gemini_api_key)
    
    # 1. 외모 설정과 스토리보드를 하나의 딕셔너리로 묶어 전달
    input_data = {
        "character_appearance": character_appearance,
        "storyboard": storyboard
    }
    context_text = json.dumps(input_data, ensure_ascii=False)
    
    # 2. 시스템 프롬프트: Danbooru 태그 변환 및 필수 태그 강제
    system_instruction = """
    너는 Animagine XL 4.0 모델에 특화된 프롬프트 엔지니어 및 Danbooru 태그 전문가야.
    제공된 '캐릭터 외모 설정'과 컷별 '지문(description)'을 결합하여, 각 컷에 맞는 긍정 프롬프트와 부정 프롬프트를 영어 태그로 작성해.
    
    [작성 규칙]
    1. 문장형이 아닌 단어(태그)들을 쉼표(,)로 구분하여 나열할 것.
    2. 긍정 프롬프트의 맨 앞에는 반드시 "masterpiece, best quality, "를 붙일 것.
    3. 그 다음 '캐릭터 외모 설정'을 영어 태그로 번역하여 넣고, 마지막에 '지문'에 해당하는 행동, 배경, 표정 태그를 넣을 것.
    4. 부정 프롬프트는 고정적으로 다음을 사용할 것: "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    5. 반드시 아래 JSON 배열 형식으로만 출력할 것. 다른 설명은 금지.
    
    [{"cut": 1, "positive_prompt": "masterpiece, best quality, 1boy, korean clothes, ...", "negative_prompt": "nsfw, lowres, ..."}]
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"데이터: {context_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3, # 프롬프트 생성은 일관성이 중요하므로 낮은 온도 유지
            )
        )
        
        # 3. JSON 정제 및 파싱
        prompts_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        prompts_list = json.loads(prompts_text)
        
        return prompts_list
        
    except Exception as e:
        print(f"프롬프트 생성 중 오류 발생: {e}")
        return []