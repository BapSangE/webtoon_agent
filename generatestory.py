# generatestory.py
from google import genai
from google.genai import types
import json

def generate_storyboard(gemini_api_key: str, parsed_data: dict) -> dict:
    """
    [Fact] 반환 타입이 list에서 dict로 변경되었습니다.
    """
    client = genai.Client(api_key=gemini_api_key)
    context_text = json.dumps(parsed_data, ensure_ascii=False)
    
    # 1. Step 1: 캐릭터 외모 설정 및 스토리보드 초안 생성
    system_instruction_1 = """
    너는 역사 웹툰 스토리 작가야. 
    제공된 독립운동가 데이터를 바탕으로 주인공의 외모를 설정하고, 20컷 미만의 웹툰 스토리보드를 작성해.
    
    [외모 설정 규칙]
    데이터에 주인공의 외모에 대한 정보가 있다면 그 정보를 바탕으로 묘사해.
    만약 외모에 대한 정보가 없다면 반드시 다음 문장으로 시작해서 묘사해: 
    "외모에 대한 정보가 없음, 보편적인 당시 외모로 작성함: (이후 상상한 구체적인 당시 복장, 머리스타일, 체격 등 묘사)"
    
    반드시 아래의 JSON 객체(Object) 형식으로만 출력하고, 다른 설명은 절대 하지 마.
    {
      "character_appearance": "외모 설정 규칙에 따른 결과 텍스트",
      "storyboard": [
        {"cut": 1, "description": "장면의 시각적 묘사 (한국어)", "dialogue": "캐릭터의 대사"}
      ]
    }
    """
    
    try:
        response_1 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"데이터: {context_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_1,
                temperature=0.7,
            )
        )
        draft_story = response_1.text
        
        # 2. Step 2: 팩트체크 및 최종 수정
        system_instruction_2 = """
        너는 엄격한 역사학자야.
        [원본 데이터]와 [웹툰 스토리 초안]을 비교해서 연도, 인물명, 업적 등 역사적 사실이 왜곡된 부분이 있다면 수정해.
        수정된 최종 결과를 초안과 똑같은 JSON 객체 형식(character_appearance와 storyboard 포함)으로만 출력해.
        마크다운(```json)을 포함하지 말고 오직 순수한 JSON 텍스트만 출력해.
        """
        
        response_2 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"[원본 데이터]: {context_text}\n\n[웹툰 스토리 초안]: {draft_story}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_2,
                temperature=0.2,
            )
        )
        final_story_text = response_2.text
        
        # 3. JSON 텍스트 정제 및 파이썬 딕셔너리로 변환
        final_story_text = final_story_text.strip().removeprefix("```json").removesuffix("```").strip()
        story_data = json.loads(final_story_text)
        
        return story_data

    except Exception as e:
        print(f"Gemini 스토리 생성 중 오류 발생: {e}")
        return {}