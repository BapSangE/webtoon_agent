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
You are a professional historical webtoon story writer and a storyboard director.
Based on the provided data of the independence activist, create a highly engaging webtoon storyboard of 6 to 10 cuts optimized for vertical scrolling.

[Webtoon Directing & Pacing Rules]
1. Vertical Scroll Flow: Utilize a cinematic flow suitable for webtoons (e.g., Cut 1: Wide establishing shot -> Cut 2: Close-up on character's determined face -> Cut 3: Action/Incident).
2. Readability: Keep 'dialogue' short and impactful, suitable for webtoon speech bubbles. Use 'narration' for time skips, historical context, or deep inner monologues.
3. Cliffhanger/Climax: The final cut MUST be highly dramatic or emotional, leaving a strong lingering impact on the reader.
4. Pacing: Condense the activist's life logically. Show clear transitions between different life stages (e.g., Youth -> Resistance -> Imprisonment/Martyrdom).

[Character & Visual Consistency Rules]
1. Define the specific appearance (age, hairstyle, outfit, props) in 'character_appearance' categorized by life stages. (e.g., [Youth] short hair, white hanbok, [Resistance] fedora, black suit).
2. Maintain strict visual consistency of the character across cuts unless a time skip occurs.
3. Avoid overly depressing or grotesque depictions; maintain a dignified and majestic tone even in hardships.

[Visual Elements for AI Generation (Bridge to Danbooru Tags)]
1. All values inside 'visual_elements' MUST be written in Danbooru-style ENGLISH TAGS (comma-separated). Do NOT use full sentences.
2. Describe objects and backgrounds explicitly (e.g., instead of "prison", use "iron bars, dark room, stone wall").
3. Specify camera angles/composition (e.g., extreme close-up, dutch angle, full body, from below) to make the webtoon dynamic.

[JSON Parsing Security Rules]
1. NEVER use double quotes (") inside the text values of 'description', 'narration', or 'dialogue'. Use single quotes (') instead.
2. If a field like narration or dialogue is not needed for a cut, leave it as an empty string (""). Do not delete the key.

Output ONLY the valid JSON object format below. Output raw JSON only without markdown formatting (do NOT wrap in ```json).

{
  "character_appearance": "시기별/상황별 주인공 상세 외모 설정 (Write in KOREAN. e.g., [청년기-25세] 검은 머리, 안경, 흰색 저고리...)",
  "storyboard": [
    {
      "cut": 1,
      "visual_elements": {
        "composition": "English tags for camera angle (e.g., wide shot, looking up, from behind)",
        "characters": "English tags for age, expression, action, specific clothes",
        "objects": "English tags for props",
        "background": "English tags for place, time, lighting, weather"
      },
      "description": "웹툰 작화를 위한 화면 연출 및 상황 요약 지문 (Write in KOREAN)",
      "narration": "상황 해설이나 독백 자막 (Write in KOREAN)",
      "dialogue": "말풍선에 들어갈 임팩트 있는 짧은 대사 (Write in KOREAN)"
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
        
        # [핵심 추가] 무료 티어 429 에러 방지를 위한 5초 강제 대기
        print("초안 생성 완료. API 호출 제한(Rate Limit) 방어를 위해 5초간 대기합니다...")
        time.sleep(5)
        
        # 2. Step 2: 팩트체크 및 최종 수정 프롬프트
        system_instruction_2 = """
너는 엄격한 역사학자이자 웹툰 스토리 검수자야.
[원본 데이터]와 [웹툰 스토리 초안]을 꼼꼼히 비교하여 연도, 인물명, 장소, 주요 업적 등 '역사적 팩트'가 왜곡된 부분이 있다면 정확하게 수정해.

[검수 및 수정 규칙]
1. 팩트 교정: 원본 데이터에 없는 허구의 역사적 사건이나 잘못된 정보가 있다면 즉시 수정해.
2. 극적 허용 인정: 역사적 팩트가 맞다면, 인물의 감정 표현, 대사의 뉘앙스, 시각적 연출(visual_elements) 등 웹툰으로서의 극적 요소는 절대 건드리지 말고 유지해.
3. 원본 유지: 검토 결과 역사적 오류가 전혀 없다면, 초안의 내용을 단 한 글자도 바꾸지 말고 그대로 반환해.

[JSON 출력 규칙]
1. 초안과 완벽하게 동일한 JSON 객체 구조(character_appearance와 storyboard(visual_elements 포함))만 반환해.
2. JSON 파싱 에러를 방지하기 위해 텍스트 값 내부에 큰따옴표(")를 절대 사용하지 마. 필요시 작은따옴표(')를 사용해.
3. 마크다운(```json) 기호나 너의 부연 설명, 인사말을 절대 포함하지 말고 오직 순수한 JSON 텍스트만 출력해.
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