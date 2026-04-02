# generatestory.py
from google import genai
from google.genai import types
import json
import time # 대기 시간을 위한 내장 라이브러리 추가

def generate_storyboard(gemini_api_key: str, parsed_data: dict) -> dict:
    client = genai.Client(api_key=gemini_api_key)
    context_text = json.dumps(parsed_data, ensure_ascii=False)
    
    # 1. Step 1: 스토리보드 초안 생성 프롬프트
    system_instruction_1 = """
    너는 역사 웹툰 스토리 작가이자 이미지 생성 AI를 위한 프롬프트 디렉터야. 
    제공된 독립운동가 데이터를 바탕으로 20컷 미만의 웹툰 스토리보드를 작성해.
    
    [외모 설정 및 사전 지식 활용 규칙]
    1. 제공된 텍스트 데이터에 물리적인 외모 묘사가 부족하더라도, 안중근(콧수염, 잘린 약지 손가락, 수의 등)이나 유관순처럼 역사적으로 널리 알려진 인물이라면 너의 역사적 사전 지식(Internal Knowledge)을 적극 동원하여 구체적으로 묘사해.
    2. 사전 지식으로도 외모를 특정할 수 없는 무명 인물일 경우에만: "보편적인 당시 외모: (당시 신분과 직업에 맞는 복장, 머리스타일, 체격)"으로 설정해.
    
    [시간 흐름에 따른 외모 변화 규칙]
    1. 인물의 일대기를 다루므로, 시간 경과(유년기->청년기->장년기) 및 상황(망명, 전투, 투옥 등)에 따른 인물의 노화, 수염 유무, 복장 변화를 반드시 설정해.
    2. 'character_appearance' 항목에 시기별/상황별 외모를 명확히 분리하여 요약해.
    3. 스토리보드의 각 컷(cut)에 해당하는 'characters' 묘사 시, 해당 컷의 시간대와 상황에 맞는 외모(나이, 옷차림)를 정확히 적용하여 작성해.
    
    [스토리 전개 및 반전 연출 규칙]
    1. 웹툰의 후반부(결말)에는 시청자의 몰입도를 극대화하고 깊은 여운을 줄 수 있는 극적인 반전(Plot Twist)을 반드시 포함해.
    2. 단, 역사적 사실(Fact)을 훼손하거나 판타지적 요소를 넣어서는 안 되며, 철저한 고증 안에서 연출적인 반전(예: 예상치 못한 인물의 정체 공개, 시점의 전환, 비장한 역사적 아이러니, 숨겨진 조력자의 희생 등)을 활용해.
    
    [시각적 묘사(Visual Elements) 및 구도 필수 규칙]
    1. 역동적인 웹툰 연출을 위해 컷마다 다양한 카메라 구도(클로즈업, 하이 앵글, 로우 앵글, 뒷모습, 파노라마, 전신 샷 등)를 반드시 설정해.
    2. 이미지 생성 AI가 고유명사를 오해하지 않도록, 모든 명사는 시각적인 형태, 색상, 재질로 풀어서 묘사해. (예: 태극기 -> 흰색 바탕에 가운데 붉은색과 푸른색의 태극 문양, 4개의 검은색 괘가 있는 깃발)
    
    [자막(내레이션) 및 대사 규칙]
    1. 대사(dialogue)로 처리하기 어색한 상황(시간 경과, 역사적 배경, 인물의 내면 심리)은 자막(narration)으로 분리해.
    2. 단, 웹툰의 몰입도와 호흡(템포)을 위해 자막을 모든 컷에 기계적으로 욱여넣지 마. 시각적 연출이나 대사만으로 충분한 컷은 자막을 과감히 생략하여 긴장감을 조절해.
    3. 컷의 상황에 따라 자막이나 대사 중 하나가 필요 없다면, JSON 키를 삭제하지 말고 반드시 빈 문자열("")로 남겨둬.
    
    반드시 아래의 JSON 객체(Object) 형식으로만 출력해.
    {
      "character_appearance": "시기별/상황별 주인공의 상세 외모 및 복장 설정 (예: [청년기] ..., [투옥기] ...)",
      "storyboard": [
        {
          "cut": 1, 
          "visual_elements": {
            "composition": "카메라 구도 및 시점 (예: 뒷모습, 클로즈업, 로우 앵글 등)",
            "characters": "해당 컷의 시간대에 맞는 인물들의 행동, 표정, 복장, 노화 상태 (주변 인물 포함)",
            "objects": "핵심 사물의 구체적인 시각적 묘사 (형태, 색상, 패턴 등 풀어서 설명)",
            "background": "장소, 시간대, 날씨, 조명(명암) 묘사"
          },
          "description": "화면에 표시될 전체 장면의 요약 지문 (한국어)", 
          "narration": "웹툰 컷 상단이나 하단에 삽입될 상황 설명 자막 또는 독백",
          "dialogue": "캐릭터의 대사"
        }
      ]
    }
    """
    
    try:
        # 첫 번째 API 호출 (초안 작성)
        response_1 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"데이터: {context_text}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_1,
                temperature=0.7,
            )
        )
        draft_story = response_1.text
        
        # [핵심 추가] 무료 티어 429 에러 방지를 위한 20초 강제 대기
        print("초안 생성 완료. API 호출 제한(Rate Limit) 방어를 위해 20초간 대기합니다...")
        time.sleep(20)
        
        # 2. Step 2: 팩트체크 및 최종 수정 프롬프트
        system_instruction_2 = """
        너는 엄격한 역사학자야.
        [원본 데이터]와 [웹툰 스토리 초안]을 비교해서 연도, 인물명, 업적 등 역사적 사실이 왜곡된 부분이 있다면 수정해.
        수정된 최종 결과를 초안과 똑같은 JSON 객체 형식(character_appearance와 storyboard(visual_elements 포함))으로만 출력해.
        마크다운(```json)을 포함하지 말고 오직 순수한 JSON 텍스트만 출력해.
        """
        
        # 두 번째 API 호출 (팩트체크)
        response_2 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"[원본 데이터]: {context_text}\n\n[웹툰 스토리 초안]: {draft_story}",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction_2,
                temperature=0.2,
            )
        )
        final_story_text = response_2.text
        
        # 3. JSON 텍스트 정제 및 파싱
        final_story_text = final_story_text.strip().removeprefix("```json").removesuffix("```").strip()
        story_data = json.loads(final_story_text)
        
        return story_data

    except Exception as e:
        print(f"Gemini 스토리 생성 중 오류 발생: {e}")
        return {}