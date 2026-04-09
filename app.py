from flask import Flask, render_template, request, jsonify
import re
import google.generativeai as genai

app = Flask(__name__)

# Gemini API 설정
GEMINI_API_KEY = "AIzaSyB5yoJCBgsGcdw7WcSDC3Dss3SFjEPVY8c"
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# 나이대 매핑
AGE_MAPPING = {
    "20대 초반": "early 20s",
    "20대 중반": "mid 20s", 
    "20대 후반": "late 20s",
    "30대 초반": "early 30s",
    "30대 중반": "mid 30s",
    "30대 후반": "late 30s",
    "40대 초반": "early 40s",
    "40대 중반": "mid 40s",
    "40대 후반": "late 40s",
    "50대 초반": "early 50s",
    "50대 중반": "mid 50s",
    "50대 후반": "late 50s"
}

# 장소 프리셋
LOCATION_PRESETS = {
    "집 거실": "sitting on a cozy beige sofa in a modern Korean apartment living room",
    "집 소파": "sitting comfortably on a soft gray sofa in a warm living room",
    "주방": "standing in a bright white kitchen in the morning",
    "카페": "sitting at a wooden table in a cozy Korean cafe with warm interior",
    "공원": "standing in a peaceful park with green trees in the background",
    "사무실": "sitting at a clean modern office desk",
    "침실": "sitting on a neatly made bed in a bright bedroom",
    "발코니": "standing on a sunny apartment balcony with plants",
    "레스토랑": "sitting at a restaurant table with soft ambient lighting",
    "헬스장": "standing in a modern gym with exercise equipment in background",
    "요가원": "sitting on a yoga mat in a peaceful studio with natural light",
    "길거리": "standing on a clean Seoul street with urban background",
    "해변": "standing on a sandy beach with ocean in the background"
}

# 의상 프리셋
CLOTHING_PRESETS = {
    "흰색 스웻셔츠": "wearing a soft white cotton sweatshirt",
    "흰색 린넨 탑": "wearing a soft white linen top",
    "베이지 니트": "wearing a cozy beige knit sweater",
    "검정 티셔츠": "wearing a simple black t-shirt",
    "운동복": "wearing comfortable athletic wear",
    "원피스": "wearing a casual one-piece dress",
    "블라우스": "wearing an elegant blouse",
    "가디건": "wearing a soft cardigan over a simple top",
    "후드티": "wearing a comfortable hoodie",
    "오프숄더": "wearing an elegant off-shoulder top",
    "흰색 오프숄더": "wearing a white off-shoulder top",
    "검정 오프숄더": "wearing a black off-shoulder top",
    "승무원 유니폼": "wearing a professional flight attendant uniform with neat scarf",
    "아나운서 스타일": "wearing a elegant news anchor style blazer and blouse, professional look",
    "정장": "wearing a formal business suit",
    "셔츠": "wearing a clean white dress shirt"
}

# 표정 프리셋
EXPRESSION_PRESETS = {
    "자연스러운 미소": "natural smile",
    "밝은 미소": "bright warm smile",
    "편안한 표정": "relaxed expression",
    "살짝 웃는": "slight gentle smile",
    "진지한": "calm focused expression"
}

# 조명 프리셋
LIGHTING_PRESETS = {
    "아침 햇살": "Warm soft morning sunlight from the window",
    "자연광": "Soft natural daylight creates even gentle lighting",
    "오후 햇살": "Warm afternoon sunlight creates a cozy golden glow",
    "실내 조명": "Soft indoor ambient lighting",
    "카페 조명": "Warm cafe lighting with soft shadows"
}

# 카메라 프리셋
CAMERA_PRESETS = {
    "아이폰 셀카": "Phone front camera selfie",
    "아이폰 후면": "iPhone back camera photo",
    "DSLR": "DSLR camera photo with shallow depth of field",
    "미러리스": "Mirrorless camera photo with natural bokeh"
}

# 목주름 프리셋
NECK_PRESETS = {
    "자연스러운": "with natural subtle neck lines",
    "목주름 있는": "with visible natural neck wrinkles",
    "목주름 없는": "with smooth neck skin"
}

# 한국어 → 영어 자동 변환 (추가 디테일용)
KOREAN_TO_ENGLISH = {
    "미니멀한 방안": "minimal room",
    "미니멀한 방": "minimal room",
    "미니멀한": "minimal",
    "미니멀": "minimal",
    "깔끔한 방": "clean room",
    "깔끔한": "clean",
    "화이트톤": "white tone",
    "흰색 벽": "white wall",
    "베이지톤": "beige tone",
    "화분이 있는": "with plants",
    "화분": "with plants",
    "식물": "plants",
    "책장": "bookshelf",
    "따뜻한 느낌": "warm atmosphere",
    "밝은 느낌": "bright atmosphere",
    "모던한 느낌": "modern style",
    "럭셔리한": "luxurious",
    "심플한": "simple",
    "파란색": "blue",
    "빨간색": "red",
    "검정색": "black",
    "흰색": "white",
    "베이지색": "beige",
    "줄무늬": "striped",
    "체크무늬": "checkered",
    "꽃무늬": "floral pattern",
    "레이스": "lace",
    "실크": "silk",
    "캐주얼한": "casual",
    "포멀한": "formal",
    "눈웃음": "smiling eyes",
    "윙크": "winking",
    "살짝 고개 기울인": "slightly tilted head",
    "턱 괴고": "chin resting on hand",
    "손 흔드는": "waving hand",
    "브이": "V sign",
    "하트": "heart gesture",
    "클로즈업": "close-up shot",
    "상반신샷": "upper body shot",
    "상반신": "upper body shot",
    "전신샷": "full body shot",
    "전신": "full body shot",
    "자연스럽게": "naturally",
    "편안하게": "comfortably",
    "고급스럽게": "elegantly"
}

# 영상 프롬프트용 발음 변환
PRONUNCIATION_CONVERT = {
    "웨하스": "웨'하'스",
    "바닐라": "바'닐'라",
    "떴다": "떠따",
    "미쳤다": "미쳐따",
    "떴습니다": "떠씁니다",
    "됐다": "돼따",
    "했다": "해따",
    "갔다": "가따",
    "왔다": "와따",
    "먹었다": "머거따",
    "봤다": "봐따"
}

# 영상 액션 변환 (한국어 → 영어)
VIDEO_ACTION_MAPPING = {
    # 등장/이동
    "뛰어들어온다": "runs into frame energetically",
    "뛰어들어와서": "runs into frame energetically",
    "뛰어들어와": "runs into frame",
    "등장함": "appears on screen",
    "등장한다": "appears on screen",
    "들어온다": "enters the frame",
    "나타난다": "appears",
    "오른쪽에서": "from the right side",
    "왼쪽에서": "from the left side",
    "위에서": "from above",
    "아래에서": "from below",
    "카메라 안보이다가": "starting off-camera then",
    # 카메라 워크
    "클로즈업": "close-up shot",
    "클로즈업하면서": "with a close-up shot",
    "줌인": "zoom in",
    "줌아웃": "zoom out",
    "상반신": "upper body shot",
    "전신": "full body shot",
    "얼굴 클로즈업": "face close-up",
    # 제품 관련
    "과자를 클로즈업하면서 보여주기": "showing the snack with a close-up shot",
    "과자를 보여주기": "showing the snack",
    "과자봉지 들고": "holding the snack bag",
    "과자봉지 한 봉지 들고": "holding one snack bag",
    "제품을 보여주면서": "while showing the product",
    "제품 들고": "holding the product",
    "한손가락으로 콕콕 가리키면서": "pointing at it with finger",
    "가리키면서": "while pointing at",
    "자랑하기": "proudly presenting",
    # 표정/감정
    "놀란거같이": "with a surprised expression",
    "놀란 표정": "surprised expression",
    "신난 표정": "excited expression",
    "웃으면서": "while smiling",
    "밝게 웃으면서": "smiling brightly",
    "진지하게": "seriously",
    "귀엽게": "cutely",
    # 동작
    "이야기한다": "talks to camera",
    "이야기하면서": "while talking",
    "말한다": "speaks",
    "설명한다": "explains",
    "먹는다": "eats",
    "먹으면서": "while eating",
    "맛있게 먹는다": "eats deliciously",
    "손 흔들면서": "while waving hand",
    "손 흔든다": "waves hand",
    "고개 끄덕이면서": "while nodding",
    "앉아있다": "sitting",
    "서있다": "standing",
    "걸어온다": "walks in",
    "다가온다": "approaches",
    # 시선
    "카메라 보면서": "looking at camera",
    "카메라를 보면서": "looking at camera",
    "정면 응시": "looking straight at camera",
    # 기타
    "처음에는": "at first",
    "그리고": "then",
    "할때": "when saying"
}

# 숫자 변환 - 고유어 (개수)
NATIVE_KOREAN_NUMBERS = {
    "1": "한", "2": "두", "3": "세", "4": "네", "5": "다섯",
    "6": "여섯", "7": "일곱", "8": "여덟", "9": "아홉", "10": "열"
}

# 숫자 변환 - 한자어 (측정)
SINO_KOREAN_NUMBERS = {
    "1": "일", "2": "이", "3": "삼", "4": "사", "5": "오",
    "6": "육", "7": "칠", "8": "팔", "9": "구", "10": "십",
    "100": "백", "1000": "천", "10000": "만"
}

# 한국어 → 영어 번역 (합성 프롬프트용) - 더 많은 표현 추가
COMPOSITE_TRANSLATIONS = {
    # 크기 관련
    "과자봉지가 너무작아": "make the snack bag much larger and more prominent",
    "너무 작아": "make it larger",
    "더 크게": "make it larger",
    "크게": "larger",
    "작게": "smaller",
    # 손 관련
    "두 손으로": "holding with both hands",
    "양손으로": "holding with both hands",
    "한 손으로": "holding with one hand",
    "왼손으로": "holding with left hand",
    "오른손으로": "holding with right hand",
    # 위치 관련
    "얼굴 옆에": "position the product next to the face",
    "얼굴옆에": "position the product next to the face",
    "가슴 높이": "at chest level",
    "눈높이": "at eye level",
    "어깨 높이": "at shoulder level",
    # 개수 관련
    "여러개": "multiple products",
    "여러 개": "multiple products",
    "두 개": "two products",
    "세 개": "three products",
    "네 개": "four products",
    "다섯 개": "five products",
    "3개": "three products",
    "2개": "two products",
    "4개": "four products",
    "5개": "five products",
    "봉지 3개": "three snack bags",
    "봉지 2개": "two snack bags",
    "봉지 4개": "four snack bags",
    "봉지 5개": "five snack bags",
    # 동작 관련
    "들고있는거로 해줘": "holding the product",
    "들고있는거로": "holding the product",
    "들고있는": "holding",
    "들고 있는": "holding",
    "보여주는": "showing",
    "가리키는": "pointing at",
    "해줘": "",
    "해주세요": "",
    "거로": "",
    # 기타
    "자연스럽게": "naturally",
    "예쁘게": "beautifully",
    "귀엽게": "cutely",
    "웃으면서": "while smiling",
    "카메라 보면서": "while looking at camera",
    "봉지": "snack bag",
    "과자": "snack",
    "화장품": "cosmetic product"
}


def translate_korean_to_english(text):
    """한국어 텍스트를 영어로 변환 - 긴 표현부터 먼저 변환"""
    if not text:
        return text
    result = text
    sorted_items = sorted(KOREAN_TO_ENGLISH.items(), key=lambda x: len(x[0]), reverse=True)
    for kr, en in sorted_items:
        result = result.replace(kr, en)
    return result


def translate_composite_text(text):
    """합성 프롬프트용 한국어 → 영어 번역"""
    if not text:
        return ""
    result = text
    # 긴 표현부터 먼저 변환
    sorted_items = sorted(COMPOSITE_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True)
    for kr, en in sorted_items:
        result = result.replace(kr, en)
    
    # 빈 문자열 정리
    result = ' '.join(result.split())
    
    # 아직 한국어가 남아있는지 확인
    if re.search('[가-힣]', result):
        # 한국어가 남아있으면 기본 영어 문장으로 감싸기
        return f"Additional detail: {result}"
    
    return result


def convert_pronunciation(text):
    """발음 변환"""
    result = text
    for kr, converted in PRONUNCIATION_CONVERT.items():
        result = result.replace(kr, converted)
    return result


def convert_numbers(text):
    """숫자를 한국어로 변환"""
    result = text
    
    # 고유어 단위 (개, 명, 봉지, 마리, 살, 잔, 그릇, 권, 켤레, 대)
    native_units = ['개', '명', '봉지', '마리', '살', '잔', '그릇', '권', '켤레', '대', '시간']
    for unit in native_units:
        pattern = rf'(\d+)\s*{unit}'
        matches = re.findall(pattern, result)
        for num in matches:
            if num in NATIVE_KOREAN_NUMBERS:
                result = re.sub(rf'{num}\s*{unit}', f'{NATIVE_KOREAN_NUMBERS[num]} {unit}', result)
    
    # 한자어 단위 (kg, g, %, 원, 배, m, L, 도, 층)
    sino_patterns = [
        (r'(\d+)\s*kg', '킬로그램'),
        (r'(\d+)\s*g', '그램'),
        (r'(\d+)\s*%', '퍼센트'),
        (r'(\d+)\s*원', '원'),
        (r'(\d+)\s*배', '배'),
        (r'(\d+)\s*ml', '밀리리터'),
    ]
    
    for pattern, unit_name in sino_patterns:
        matches = re.findall(pattern, result)
        for num in matches:
            num_str = num
            if int(num) >= 100:
                converted = ""
                n = int(num)
                if n >= 10000:
                    converted += f"{SINO_KOREAN_NUMBERS.get(str(n // 10000), str(n // 10000))}만"
                    n = n % 10000
                if n >= 1000:
                    converted += f"{SINO_KOREAN_NUMBERS.get(str(n // 1000), '')}천"
                    n = n % 1000
                if n >= 100:
                    converted += f"{SINO_KOREAN_NUMBERS.get(str(n // 100), '')}백"
                    n = n % 100
                if n >= 10:
                    converted += f"{SINO_KOREAN_NUMBERS.get(str(n // 10), '')}십"
                    n = n % 10
                if n > 0:
                    converted += SINO_KOREAN_NUMBERS.get(str(n), str(n))
                result = re.sub(pattern.replace(r'(\d+)', num_str), f'{converted} {unit_name}', result)
            elif num in SINO_KOREAN_NUMBERS:
                result = re.sub(pattern.replace(r'(\d+)', num_str), f'{SINO_KOREAN_NUMBERS[num]} {unit_name}', result)
    
    # 1+1 -> 원플원
    result = result.replace('1+1', '원플원')
    result = result.replace('2+1', '투플원')
    
    return result


def parse_korean_input(user_input):
    result = {
        "gender": "여성",
        "age": "40대 초반",
        "clothing": "",
        "location": "",
        "expression": "자연스러운 미소",
        "lighting": "자연광",
        "camera": "아이폰 셀카",
        "neck": ""
    }
    
    if "남자" in user_input or "남성" in user_input:
        result["gender"] = "남성"
    
    for age_kr in AGE_MAPPING.keys():
        if age_kr in user_input:
            result["age"] = age_kr
            break
    
    for loc_kr in LOCATION_PRESETS.keys():
        if loc_kr in user_input or loc_kr.replace(" ", "") in user_input.replace(" ", ""):
            result["location"] = loc_kr
            break
    
    for cloth_kr in CLOTHING_PRESETS.keys():
        if cloth_kr in user_input or cloth_kr.replace(" ", "") in user_input.replace(" ", ""):
            result["clothing"] = cloth_kr
            break
    
    return result


def generate_prompt(parsed_data, custom_details=""):
    age_en = AGE_MAPPING.get(parsed_data["age"], "early 40s")
    gender = "woman" if parsed_data.get("gender", "여성") == "여성" else "man"
    pronoun = "She" if gender == "woman" else "He"
    pronoun_pos = "her" if gender == "woman" else "his"
    
    camera = CAMERA_PRESETS.get(parsed_data.get("camera", "아이폰 셀카"), CAMERA_PRESETS["아이폰 셀카"])
    if parsed_data.get("camera_detail"):
        camera += f", {translate_korean_to_english(parsed_data['camera_detail'])}"
    
    if parsed_data["clothing"] in CLOTHING_PRESETS:
        clothing_desc = CLOTHING_PRESETS[parsed_data["clothing"]]
    elif parsed_data["clothing"]:
        clothing_desc = f"wearing {parsed_data['clothing']}"
    else:
        clothing_desc = "wearing casual comfortable clothing"
    if parsed_data.get("clothing_detail"):
        clothing_desc += f", {translate_korean_to_english(parsed_data['clothing_detail'])}"
    
    if parsed_data["location"] in LOCATION_PRESETS:
        location_desc = LOCATION_PRESETS[parsed_data["location"]]
    else:
        location_desc = "in a bright modern Korean home"
    if parsed_data.get("location_detail"):
        location_desc += f", {translate_korean_to_english(parsed_data['location_detail'])}"
    
    lighting_desc = LIGHTING_PRESETS.get(parsed_data.get("lighting", "자연광"), LIGHTING_PRESETS["자연광"])
    
    expression = EXPRESSION_PRESETS.get(parsed_data.get("expression", "자연스러운 미소"), "natural smile")
    if parsed_data.get("expression_detail"):
        expression += f", {translate_korean_to_english(parsed_data['expression_detail'])}"
    
    neck_desc = ""
    if parsed_data.get("neck") and parsed_data["neck"] in NECK_PRESETS:
        neck_desc = ", " + NECK_PRESETS[parsed_data["neck"]]
    
    if custom_details:
        custom_details = translate_korean_to_english(custom_details)
    
    lines = [
        f"{camera}, Korean {gender} in {pronoun_pos} {age_en}",
        f"natural skin texture, minimal makeup{neck_desc}",
        f"{clothing_desc}",
        f"{location_desc}",
        f"looking directly at camera, relaxed natural posture",
        f"{lighting_desc}",
        f"clean minimal background, airy atmosphere",
        f"candid relaxed {expression}",
        f"photo-realistic, high-resolution, no motion blur",
        f"vertical 9:16 aspect ratio for Instagram Reels"
    ]
    
    if custom_details:
        lines.insert(-1, translate_korean_to_english(custom_details))
    
    prompt = "\n".join(lines)
    return prompt


def convert_action_to_english(action_text):
    """한국어 액션 설명을 영어로 변환"""
    if not action_text:
        return ""
    
    result = action_text.strip()
    
    # 긴 표현부터 먼저 변환
    sorted_items = sorted(VIDEO_ACTION_MAPPING.items(), key=lambda x: len(x[0]), reverse=True)
    for kr, en in sorted_items:
        result = result.replace(kr, en)
    
    # 남은 한국어가 있으면 기본 문장으로 감싸기
    if re.search('[가-힣]', result):
        # 일부 변환된 경우 그대로 사용
        return f"Action: {result}"
    
    return result


def generate_video_prompt(scene_data, options):
    """영상 프롬프트 생성"""
    gender = "woman" if options.get('gender', '여성') == '여성' else "man"
    pronoun = "She" if gender == "woman" else "He"
    pronoun_pos = "her" if gender == "woman" else "his"
    age = options.get('age', '26살')
    product = options.get('product', 'snack bag')
    
    scene_num = scene_data.get('scene_num', 1)
    action = scene_data.get('action', '')
    dialogue = scene_data.get('dialogue', '')
    
    # 액션을 영어로 변환
    action_en = convert_action_to_english(action)
    
    # 발음 변환 및 숫자 변환
    dialogue = convert_pronunciation(dialogue)
    dialogue = convert_numbers(dialogue)
    
    lines = [
        f"Ultra-realistic cinematic 4K HDR 9:16 video.",
        f"Korean {gender}, age {age}, from the reference image.",
        f"Identical face, hairstyle, outfit, and background.",
    ]
    
    # 액션이 있으면 추가
    if action_en:
        lines.append("")
        lines.append(action_en)
    
    lines.extend([
        "",
        f'{pronoun} speaks naturally in Korean:',
        f'"{dialogue}"',
        "",
        f"Natural body language throughout.",
        f"Bright, clean lighting.",
        "",
        f"No subtitles, on-screen text, music, background music, sound effects, or audio effects.",
        f"Full 9:16 vertical format."
    ])
    
    return "\n".join(lines)


# ===== 라우트 정의 =====

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_input = data.get('input', '')
    custom_details = data.get('custom_details', '')
    
    if not user_input:
        return jsonify({'error': '입력을 해주세요'}), 400
    
    parsed = parse_korean_input(user_input)
    prompt = generate_prompt(parsed, custom_details)
    
    return jsonify({'prompt': prompt, 'parsed': parsed})


@app.route('/generate_custom', methods=['POST'])
def generate_custom():
    data = request.json
    
    parsed = {
        "gender": data.get('gender', '여성'),
        "age": data.get('age', '40대 초반'),
        "clothing": data.get('clothing', ''),
        "location": data.get('location', ''),
        "expression": data.get('expression', '자연스러운 미소'),
        "lighting": data.get('lighting', '자연광'),
        "camera": data.get('camera', '아이폰 셀카'),
        "neck": data.get('neck', ''),
        "camera_detail": data.get('camera_detail', ''),
        "clothing_detail": data.get('clothing_detail', ''),
        "location_detail": data.get('location_detail', ''),
        "expression_detail": data.get('expression_detail', '')
    }
    
    custom_details = data.get('custom_details', '')
    prompt = generate_prompt(parsed, custom_details)
    
    return jsonify({'prompt': prompt, 'parsed': parsed})


@app.route('/generate_video', methods=['POST'])
def generate_video():
    data = request.json
    
    plan_text = data.get('plan', '')
    options = {
        'gender': data.get('gender', '여성'),
        'age': data.get('age', '26살'),
        'product': data.get('product', 'snack bag')
    }
    
    # Gemini AI로 프롬프트 생성
    gender_en = "woman" if options['gender'] == '여성' else "man"
    pronoun = "She" if gender_en == "woman" else "He"
    
    system_prompt = f"""당신은 AI 영상 생성 프롬프트 전문가입니다.
사용자가 한국어 기획안을 주면, 각 씬(#1, #2 등)별로 영상 생성 프롬프트를 만들어주세요.

## 규칙:
1. 각 씬마다 별도의 프롬프트 생성
2. 프롬프트는 영어로 작성 (대사 부분만 한국어 유지)
3. 한 줄당 최대 20단어
4. 9:16 세로 영상 포맷

## 대사 변환 규칙 (매우 중요!):
- 숫자+개/명/봉지/마리 → 고유어 (1개→한 개, 3봉지→세 봉지)
- 숫자+kg/g/%/원 → 한자어 (3kg→삼 킬로그램, 5000원→오천 원)
- 1+1 → 원플원, 2+1 → 투플원
- 웨하스 → 웨'하'스, 바닐라 → 바'닐'라
- 떴다 → 떠따, 됐다 → 돼따, 했다 → 해따

## 인물 정보:
- 성별: Korean {gender_en}
- 나이: {options['age']}
- 제품: {options['product']}

## 출력 형식 (각 씬마다):
```
[SCENE_1]
Ultra-realistic cinematic 4K HDR 9:16 video.
Korean {gender_en}, age {options['age']}, from the reference image.
Identical face, hairstyle, outfit, and background.

(여기에 액션/카메라 워크 설명 - 영어로)

{pronoun} speaks naturally in Korean:
"(변환된 한국어 대사)"

Natural body language throughout.
Bright, clean lighting.

No subtitles, on-screen text, music, background music, sound effects, or audio effects.
Full 9:16 vertical format.
[/SCENE_1]
```

기획안의 괄호() 안 내용은 액션/연출 지시이고, 나머지는 대사입니다.
액션은 영어로 자연스럽게 변환하세요 (예: "뛰어들어온다" → "runs into frame energetically").
"""

    user_prompt = f"다음 기획안을 씬별 영상 프롬프트로 변환해주세요:\n\n{plan_text}"
    
    try:
        response = gemini_model.generate_content([
            {"role": "user", "parts": [system_prompt + "\n\n" + user_prompt]}
        ])
        
        ai_response = response.text
        
        # 씬별로 파싱
        prompts = []
        scene_pattern = r'\[SCENE_(\d+)\](.*?)\[/SCENE_\d+\]'
        matches = re.findall(scene_pattern, ai_response, re.DOTALL)
        
        if matches:
            for scene_num, content in matches:
                prompts.append({
                    'scene_num': int(scene_num),
                    'prompt': content.strip()
                })
        else:
            # 파싱 실패시 전체 응답 반환
            prompts.append({
                'scene_num': 1,
                'prompt': ai_response
            })
        
        return jsonify({'prompts': prompts, 'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'translated': ''})
    
    result = translate_composite_text(text)
    return jsonify({'translated': result})


# ===== 앱 실행 =====
if __name__ == '__main__':
    app.run(debug=True, port=5002)
