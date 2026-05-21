import json
import google.generativeai as genai

def generate_image_prompts(gemini_api_key: str, character_appearance: str, storyboard: list):
    genai.configure(api_key=gemini_api_key)
    
    # [수정됨] 부정 프롬프트 고정값 (파이썬 변수로 분리)
    BASE_NEGATIVE_PROMPT = "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, blurry, abstract background, simple background, fantasy clothes, fusion hanbok, lace, ribbons, frills, miniskirt, kimono, hanfu, modern clothes, japanese clothes, japanese architecture, samurai, ninja, emaciated, zombie, pale, sick, dark circles, messy dirt on face, horror, gloomy, ugly"

    # [수정됨] 최적화된 시스템 프롬프트 (부정 프롬프트 생성 제외)
    system_instruction = """
You are a prompt engineer specialized in the Animagine XL 4.0 model and an expert in Danbooru tags.
Perfectly analyze the provided 'character_appearance' and the 'visual_elements' for each cut, and write the positive prompts in English tags for each cut.

[Writing Rules]
1. List tags separated by commas (,). Do NOT use full sentences.
2. The absolute beginning of the positive prompt MUST be exactly: "masterpiece, best quality, very aesthetic, absurdres, comic, webtoon, lineart, "
3. Tag ordering: Character Appearance -> composition -> characters (expression/action) -> objects -> background.
4. Refine and optimize the input English tags from 'visual_elements' to strictly fit the Danbooru tag syntax.
5. Apply weights to key objects or unique compositions (e.g., (white flag:1.3)).
6. [Historical Hanbok Rule] To prevent fusion/modernized hanbok, you MUST include gender-specific tags: (Male: korean clothes, hanbok, durumagi / Female: korean clothes, hanbok, jeogori, long chima).
7. [Face Preservation] If the input composition is a "full body" or "wide shot", you MUST append "(detailed face:1.2), (highly detailed eyes:1.1)" to prevent facial distortion.
8. [Art Style Control] Maintain a dignified and majestic depiction. Depicting a ruined or overly gloomy state is strictly forbidden. Use tags like "dignified", "determined expression".
9. [Lighting & Tone] When writing background tags, you MUST include lighting tags suitable for the time and atmosphere (e.g., cinematic lighting, sunlight, night, cloudy) to add depth.
10. Do not write negative prompts. Output ONLY the positive prompts in the JSON array format below. Output raw JSON only without markdown formatting.

[
  {"cut": 1, "positive_prompt": "masterpiece, best quality, very aesthetic, absurdres, comic, webtoon, lineart, 1boy, (25-year-old:1.3), dignified, determined expression, upper body, cinematic lighting, ..."}
]
"""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction,
        generation_config={"response_mime_type": "application/json"}
    )

    prompt_content = f"""
    [캐릭터 외모 설정]
    {character_appearance}

    [컷별 스토리보드]
    {json.dumps(storyboard, ensure_ascii=False, indent=2)}
    """

    try:
        response = model.generate_content(prompt_content)
        parsed_prompts = json.loads(response.text)
        
        # [추가됨] 파이썬 로직에서 부정 프롬프트를 일괄 병합
        for p in parsed_prompts:
            p['negative_prompt'] = BASE_NEGATIVE_PROMPT
            
        return parsed_prompts

    except Exception as e:
        print(f"프롬프트 생성 중 오류 발생: {e}")
        return None