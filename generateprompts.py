import json
import google.generativeai as genai

def generate_image_prompts(gemini_api_key: str, character_appearance: str, storyboard: list):
    genai.configure(api_key=gemini_api_key)
    
    # [수정됨] 부정 프롬프트 고정값 (파이썬 변수로 분리)
    BASE_NEGATIVE_PROMPT = "nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, blurry, abstract background, simple background, fantasy clothes, fusion hanbok, lace, ribbons, frills, miniskirt, kimono, hanfu, modern clothes, japanese clothes, japanese architecture, samurai, ninja, emaciated, zombie, pale, sick, dark circles, messy dirt on face, horror, gloomy, ugly"

    # [수정됨] 최적화된 시스템 프롬프트 (부정 프롬프트 생성 제외)
    system_instruction = """
    너는 Animagine XL 4.0 모델에 특화된 프롬프트 엔지니어 및 Danbooru 태그 전문가야.
    제공된 '캐릭터 외모 설정'과 컷별 'visual_elements'를 완벽하게 분석하여, 각 컷에 맞는 긍정 프롬프트를 영어 태그로 작성해.

    [작성 규칙]
    1. 문장형이 아닌 단어/구문 태그들을 쉼표(,)로 구분하여 나열할 것.
    2. 긍정 프롬프트 맨 앞: "masterpiece, best quality, "
    3. 태그 작성 순서: 캐릭터 외모 -> composition(구도/시점) -> characters(표정/행동) -> objects(사물) -> background(배경/조명) 순.
    4. composition의 한국어 구도 묘사는 Danbooru 전용 카메라 태그로 번역.
    5. 핵심 사물이나 특이한 구도에는 가중치 부여 (예: (white flag:1.3)).
    6. [한복 고증] 퓨전 한복을 막기 위해 성별에 따라 태그 포함. (남성: korean clothes, hanbok, durumagi / 여성: korean clothes, hanbok, jeogori, long chima)
    7. [얼굴 뭉개짐 방지] 인물 컷에서는 "upper body", "cowboy shot", "close-up" 중 하나를 반드시 포함하고, "full body", "wide shot"은 절대 금지.
    8. [화풍 통제] 단정하고 위엄 있는 묘사 유지. 피폐한 묘사 금지. ("dignified", "determined expression" 등 활용)
    9. [조명 및 톤앤매너] background 태그 작성 시 컷의 시간대와 분위기에 맞는 조명 태그(예: cinematic lighting, sunlight, night, cloudy 등)를 반드시 포함하여 입체감을 살릴 것.
    10. 부정 프롬프트는 작성하지 마. 오직 긍정 프롬프트만 아래 JSON 배열 형식으로 출력해.

    [{"cut": 1, "positive_prompt": "masterpiece, best quality, 1boy, upper body, dignified, determined expression, cinematic lighting, ..."}]
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