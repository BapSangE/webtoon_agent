# generatestory.py
from google import genai
from google.genai import types
import json
import time # 대기 시간을 위한 내장 라이브러리 추가

def generate_storyboard(gemini_api_key: str, parsed_data: dict) -> dict:
    client = genai.Client(api_key=gemini_api_key)
    context_text = json.dumps(parsed_data, ensure_ascii=False)
    
    # 1. Step 1: 스토리보드 초안 생성 프롬프트
    system_instruction_1 = system_instruction = """
You are a historical webtoon story writer and a prompt director for an AI image generator.
Based on the provided data of the independence activist, create a storyboard of fewer than 20 cuts.

[Appearance & Background Knowledge Rules]
1. Even if the provided text lacks physical descriptions, if the person is historically well-known (e.g., Ahn Jung-geun's mustache, missing ring finger, prison uniform), actively use your internal historical knowledge to describe them specifically.
2. Only for unknown figures with no available physical data: set as "Common appearance of the era: (attire, hairstyle, physique fitting their social status)".

[★CORE: Time-lapse & Visual Consistency Rules]
1. Since this is a biography, you MUST set the aging process, facial hair, and outfit changes according to the passage of time (Childhood -> Youth -> Adulthood) and situations (Exile, Battle, Imprisonment).
2. Categorize the appearance by period/situation in the 'character_appearance' field. Use specific numerical ages, colors, and materials instead of vague adjectives.
3. When describing 'characters' in each cut, you MUST maintain strict visual consistency of age, facial features, and outfit colors from the previous cut, unless there is an explicit time skip.

[Plot Twist & Directing Rules]
1. The ending MUST include a dramatic plot twist to maximize immersion and leave a lingering impact.
2. Do not distort historical facts or add fantasy elements. Use directing twists (e.g., unexpected identity reveal, shift in perspective, hidden sacrifice) within strict historical accuracy.

[Visual Elements & Camera Rules]
1. Set diverse camera angles (close-up, high angle, low angle, back view, panorama, full body shot) for dynamic directing.
2. Describe all nouns visually (shapes, colors, patterns) so the image AI does not misinterpret proper nouns. (e.g., instead of Taegeukgi -> a flag with a white background, red and blue Taegeuk circle, and four black trigrams).
3. To directly feed the Stable Diffusion image generator, all values inside 'visual_elements' MUST be written in ENGLISH TAGS (comma-separated).

[Narration & Dialogue Rules]
1. Separate situations that are awkward as dialogue (time skips, historical background, inner thoughts) into 'narration'.
2. Do not force narration into every cut. Omit it if visual directing or dialogue is sufficient to control the pacing.
3. If narration or dialogue is unnecessary for a cut, leave the JSON value as an empty string (""), do not delete the key.

You MUST output ONLY the following JSON object format. Do not include markdown blocks or any other text.
{
  "character_appearance": "시기별/상황별 주인공의 상세 외모 및 복장 설정 (Write in KOREAN. e.g., [청년기-25세] 검은 머리, 쪽빛 저고리...)",
  "storyboard": [
    {
      "cut": 1, 
      "visual_elements": {
        "composition": "Camera angle and viewpoint (Write in ENGLISH tags. e.g., close-up, low angle, looking at viewer)",
        "characters": "Specific age, expression, outfit, action of characters (Write in ENGLISH tags, maintain consistency with previous cut)",
        "objects": "Visual description of key props (Write in ENGLISH tags)",
        "background": "Place, time, weather, lighting (Write in ENGLISH tags)"
      },
      "description": "화면에 표시될 전체 장면의 요약 지문 (Write in KOREAN)", 
      "narration": "웹툰 컷 상단이나 하단에 삽입될 상황 설명 자막 또는 독백 (Write in KOREAN)",
      "dialogue": "캐릭터의 대사 (Write in KOREAN)"
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