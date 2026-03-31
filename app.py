import streamlit as st
import openai
import json
import difflib
from datetime import datetime
import os

st.set_page_config(page_title="ReText – Content Surgeon", page_icon="✂️")

PASSWORD = "retext2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        pwd = st.text_input("Enter password to access ReText:", type="password")
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("Invalid password")
        st.stop()

check_password()

# ==================== МНОГОЯЗЫЧНЫЙ ИНТЕРФЕЙС ====================

LANGUAGES = {
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
    "🇩🇪 Deutsch": "de",
    "🇫🇷 Français": "fr",
    "🇪🇸 Español": "es",
    "🇨🇳 中文": "zh",
    "🇦🇱 Shqip": "sq",
    "🇷🇸 Srpski": "sr",
    "🇨🇿 Čeština": "cs",
    "🇵🇱 Polski": "pl",
    "🇭🇺 Magyar": "hu"
}

# Типы контента
CONTENT_TYPES = {
    "ru": ["📄 Коммерческие предложения (B2B)", "🔬 Научные/технические пресс-релизы"],
    "en": ["📄 Business Proposals (B2B)", "🔬 Scientific/Technical Press Releases"],
    "de": ["📄 Geschäftsangebote (B2B)", "🔬 Wissenschaftliche/Technische Pressemitteilungen"],
    "fr": ["📄 Propositions commerciales (B2B)", "🔬 Communiqués de presse scientifiques/techniques"],
    "es": ["📄 Propuestas comerciales (B2B)", "🔬 Comunicados de prensa científicos/técnicos"],
    "zh": ["📄 商业提案 (B2B)", "🔬 科学/技术新闻稿"],
    "sq": ["📄 Propozime biznesi (B2B)", "🔬 Njoftime për shtyp shkencore/teknike"],
    "sr": ["📄 Poslovne ponude (B2B)", "🔬 Naučna/tehnička saopštenja za štampu"],
    "cs": ["📄 Obchodní nabídky (B2B)", "🔬 Vědecké/technické tiskové zprávy"],
    "pl": ["📄 Oferty biznesowe (B2B)", "🔬 Naukowe/techniczne komunikaty prasowe"],
    "hu": ["📄 Üzleti ajánlatok (B2B)", "🔬 Tudományos/műszaki sajtóközlemények"]
}

# Расширенные аудиторные группы
AUDIENCE_OPTIONS = {
    "ru": {
        "business": [
            "👔 ЛПР (CEO, директор)",
            "⚙️ Технари (инженеры, разработчики, R&D)",
            "📢 Маркетологи и PR",
            "💰 Инвесторы (фонды, бизнес-ангелы)",
            "👥 Массовая аудитория (широкая публика)",
            "🎯 Потенциальные сотрудники (найм)",
            "🏢 Покупатели B2B (корпоративные клиенты)",
            "🛍️ Покупатели B2C (конечные потребители)"
        ],
        "scientific": [
            "🔬 Научные редакторы и журналисты",
            "⚙️ R&D-директора и технические эксперты",
            "💰 Инвесторы в deep tech",
            "👥 Широкая публика (научпоп)",
            "🎯 Потенциальные сотрудники (найм научных кадров)",
            "🏢 Промышленные партнеры (B2B)",
            "🛍️ Потребители технологий (B2C)"
        ]
    },
    "en": {
        "business": [
            "👔 Executive (CEO, Director)",
            "⚙️ Technical (Engineers, Developers, R&D)",
            "📢 Marketing & PR",
            "💰 Investor (VC, Angel)",
            "👥 General Public",
            "🎯 Potential Employees (Recruitment)",
            "🏢 B2B Buyers (Corporate Clients)",
            "🛍️ B2C Buyers (End Consumers)"
        ],
        "scientific": [
            "🔬 Science Editors & Journalists",
            "⚙️ R&D Directors & Technical Experts",
            "💰 Deep Tech Investors",
            "👥 General Public (Science Enthusiasts)",
            "🎯 Potential Employees (Scientific Recruitment)",
            "🏢 Industrial Partners (B2B)",
            "🛍️ Technology Consumers (B2C)"
        ]
    }
}

# Стилистические инструкции для каждой аудитории
AUDIENCE_STYLE_GUIDE = {
    "ru": {
        "👔 ЛПР (CEO, директор)": "Лаконично, стратегически. Фокус на ROI, эффективность, сроки окупаемости, конкурентные преимущества. Без технических деталей. Язык решений, а не процессов.",
        "⚙️ Технари (инженеры, разработчики, R&D)": "Точно, детально, с цифрами и фактами. Используй профессиональную терминологию. Фокус на технические характеристики, архитектуру, reproducibility. Доверие через точность.",
        "📢 Маркетологи и PR": "Ярко, образно, с акцентами на вовлечение и историю. Используй метафоры, контрасты, примеры. Фокус на уникальность, новизну, медийный потенциал.",
        "💰 Инвесторы (фонды, бизнес-ангелы)": "Фокус на потенциал роста, масштабирование, TAM, unit-экономику, защиту интеллектуальной собственности, exit strategy. Рационально, без эйфории.",
        "👥 Массовая аудитория (широкая публика)": "Просто, доступно, эмоционально. Избегай терминов. Фокус на выгоду для обычного человека, эмоции, понятные аналогии.",
        "🎯 Потенциальные сотрудники (найм)": "Вдохновляюще, о миссии, культуре, развитии, команде. Фокус на возможности роста, интересные задачи, влияние на мир. Язык приглашения, не продажи.",
        "🏢 Покупатели B2B (корпоративные клиенты)": "Рационально, о выгоде, надёжности, окупаемости, поддержке, интеграции. Фокус на снижение рисков и повышение эффективности бизнеса клиента.",
        "🛍️ Покупатели B2C (конечные потребители)": "Эмоционально, о пользе, простоте, выгоде для себя. Фокус на решение личных проблем, удобство, статус, впечатления.",
        # Scientific
        "🔬 Научные редакторы и журналисты": "Аккуратно, фактологически точно. Фокус на новизну, воспроизводимость, значимость для научного сообщества. Язык научных публикаций, но без перегруза.",
        "⚙️ R&D-директора и технические эксперты": "Глубоко, технически точно. Фокус на методологию, инновационность, применимость в R&D, защиту IP. Доверие через детали.",
        "💰 Инвесторы в deep tech": "Фокус на технологическую уникальность, патенты, рынок, команду, барьеры входа. Язык технологических инвестиций.",
        "👥 Широкая публика (научпоп)": "Увлекательно, доступно, образно. Фокус на удивление, практическое значение, понятные аналогии. Как статья в хорошем научпоп-медиа.",
        "🎯 Потенциальные сотрудники (найм научных кадров)": "Вдохновляюще, о научных вызовах, оборудовании, коллаборациях, публикациях, возможностях роста.",
        "🏢 Промышленные партнеры (B2B)": "О прикладной ценности, масштабируемости технологии, лицензировании, совместных разработках. Язык технологического трансфера.",
        "🛍️ Потребители технологий (B2C)": "О том, как технология меняет жизнь: проще, быстрее, интереснее, безопаснее. Эмоционально, без терминов."
    },
    "en": {
        "👔 Executive (CEO, Director)": "Concise, strategic. Focus on ROI, efficiency, payback period, competitive advantage. No technical details. Language of decisions, not processes.",
        "⚙️ Technical (Engineers, Developers, R&D)": "Precise, detailed, with numbers and facts. Use professional terminology. Focus on technical specifications, architecture, reproducibility.",
        "📢 Marketing & PR": "Vivid, figurative, focused on engagement and storytelling. Use metaphors, contrasts, examples. Focus on uniqueness, novelty, media potential.",
        "💰 Investor (VC, Angel)": "Focus on growth potential, scalability, TAM, unit economics, IP protection, exit strategy. Rational, no hype.",
        "👥 General Public": "Simple, accessible, emotional. Avoid jargon. Focus on benefits for ordinary people, emotions, relatable analogies.",
        "🎯 Potential Employees (Recruitment)": "Inspiring, about mission, culture, growth, team. Focus on opportunities, interesting challenges, impact. Language of invitation.",
        "🏢 B2B Buyers (Corporate Clients)": "Rational, about benefits, reliability, ROI, support, integration. Focus on reducing risks and improving client's business efficiency.",
        "🛍️ B2C Buyers (End Consumers)": "Emotional, about benefits, simplicity, personal gain. Focus on solving personal problems, convenience, status, experience.",
        # Scientific
        "🔬 Science Editors & Journalists": "Precise, fact-based. Focus on novelty, reproducibility, significance for scientific community. Language of scientific publications.",
        "⚙️ R&D Directors & Technical Experts": "Deep, technically precise. Focus on methodology, innovativeness, applicability in R&D, IP protection. Trust through detail.",
        "💰 Deep Tech Investors": "Focus on technological uniqueness, patents, market, team, barriers to entry. Language of technology investments.",
        "👥 General Public (Science Enthusiasts)": "Engaging, accessible, vivid. Focus on wonder, practical significance, relatable analogies. Like a good science article.",
        "🎯 Potential Employees (Scientific Recruitment)": "Inspiring, about scientific challenges, equipment, collaborations, publications, growth opportunities.",
        "🏢 Industrial Partners (B2B)": "About applied value, scalability, licensing, joint development. Language of technology transfer.",
        "🛍️ Technology Consumers (B2C)": "About how technology changes life: easier, faster, more interesting, safer. Emotional, no jargon."
    }
}

# Структуры для разных типов контента (оставлены как в предыдущей версии)
STRUCTURES = {
    "business": {
        "ru": """
Структура идеального коммерческого предложения:
1. Боль (понятная клиенту проблема)
2. Решение (одним предложением, УТП)
3. Как это работает (механизм)
4. Доказательства (кейс, цифры)
5. Цена и условия
6. Призыв к действию (однозначный)
""",
        "en": """
Ideal business proposal structure:
1. Pain (clear client problem)
2. Solution (one sentence, USP)
3. How it works (mechanism)
4. Proof (case, numbers)
5. Price and terms
6. Call to action (unambiguous)
"""
    },
    "scientific": {
        "ru": """
Структура идеального научного/технического пресс-лиза:
1. Заголовок-сенсация (главное открытие одним предложением)
2. Лид (кто, что, где, когда, почему это важно)
3. Контекст и актуальность проблемы
4. Методология и подход (как это сделали)
5. Ключевые результаты и доказательства (цифры, данные)
6. Значимость для науки/индустрии/общества
7. Цитаты исследователей или экспертов
8. Контактная информация и ссылки на публикации
""",
        "en": """
Ideal scientific/technical press release structure:
1. Headline (the main discovery in one sentence)
2. Lead (who, what, where, when, why it matters)
3. Context and relevance of the problem
4. Methodology and approach (how it was done)
5. Key results and evidence (data, numbers)
6. Significance for science/industry/society
7. Quotes from researchers or experts
8. Contact information and publication links
"""
    }
}

# Тексты интерфейса (базовые)
TEXTS = {
    "ru": {
        "title": "✂️ ReText – Контент-хирург",
        "subtitle": "Переделываем тексты под любую аудиторию: продажи, найм, наука, PR.",
        "settings": "Настройки",
        "language": "Язык интерфейса",
        "content_type": "Тип контента",
        "tone_params": "Параметры тональности",
        "audience": "Аудитория",
        "emotionality": "Эмоциональность",
        "emotionality_options": ["низкая", "средняя", "высокая"],
        "complexity": "Сложность",
        "complexity_options": ["простая", "средняя", "высокая"],
        "speed": "Скорость/ритм",
        "speed_options": ["ритмичная", "размеренная", "прерывистая"],
        "literary_editing": "Литературное редактирование",
        "literary_editing_help": "Убирает повторы, тавтологию, улучшает стиль",
        "text_input_label": "Вставьте текст:",
        "run_button": "🚀 Запустить ReText",
        "spinner1": "1/6 Смысловая диагностика...",
        "spinner2": "2/6 Реструктуризация...",
        "spinner3": "3/6 Настройка тональности и стиля под аудиторию...",
        "spinner4": "4/6 Добавление вовлекающих элементов...",
        "spinner5": "5/6 Литературное редактирование...",
        "spinner6": "6/6 Формирование отчёта...",
        "diagnosis_title": "🔍 Смысловая диагностика",
        "main_thesis": "**Главная мысль:**",
        "diagnosis": "**Диагноз:**",
        "redundant_parts": "**Лишние части:**",
        "correct_thesis": "Если главная мысль неверна, исправьте:",
        "using_thesis": "Будем использовать:",
        "success": "Готово!",
        "tab_result": "📄 Стало",
        "tab_report": "📊 Отчёт",
        "tab_diff": "🔍 Визуальное сравнение",
        "tab_original": "📜 Было",
        "session_count": "Сессий:",
        "warning_empty": "Пожалуйста, введите текст."
    },
    "en": {
        "title": "✂️ ReText – Content Surgeon",
        "subtitle": "Rewrite texts for any audience: sales, recruitment, science, PR.",
        "settings": "Settings",
        "language": "Interface language",
        "content_type": "Content type",
        "tone_params": "Tone parameters",
        "audience": "Audience",
        "emotionality": "Emotionality",
        "emotionality_options": ["low", "medium", "high"],
        "complexity": "Complexity",
        "complexity_options": ["simple", "medium", "complex"],
        "speed": "Pacing",
        "speed_options": ["rhythmic", "measured", "jerky"],
        "literary_editing": "Literary editing",
        "literary_editing_help": "Removes repetitions, tautology, improves style",
        "text_input_label": "Paste your text:",
        "run_button": "🚀 Run ReText",
        "spinner1": "1/6 Sense diagnosis...",
        "spinner2": "2/6 Restructuring...",
        "spinner3": "3/6 Tone & style adjustment for audience...",
        "spinner4": "4/6 Adding engagement elements...",
        "spinner5": "5/6 Literary editing...",
        "spinner6": "6/6 Generating report...",
        "diagnosis_title": "🔍 Sense diagnosis",
        "main_thesis": "**Main thesis:**",
        "diagnosis": "**Diagnosis:**",
        "redundant_parts": "**Redundant parts:**",
        "correct_thesis": "If main thesis is incorrect, correct it:",
        "using_thesis": "Will use:",
        "success": "Done!",
        "tab_result": "📄 Result",
        "tab_report": "📊 Report",
        "tab_diff": "🔍 Visual comparison",
        "tab_original": "📜 Original",
        "session_count": "Sessions:",
        "warning_empty": "Please enter text."
    }
}

def get_text(key, lang_code):
    if lang_code in TEXTS and key in TEXTS[lang_code]:
        return TEXTS[lang_code][key]
    return TEXTS["en"].get(key, key)

def get_audience_options(content_type, lang_code):
    if lang_code in AUDIENCE_OPTIONS:
        if content_type in AUDIENCE_OPTIONS[lang_code]:
            return AUDIENCE_OPTIONS[lang_code][content_type]
    return AUDIENCE_OPTIONS["en"][content_type]

def get_audience_style_guide(audience, lang_code):
    if lang_code in AUDIENCE_STYLE_GUIDE:
        if audience in AUDIENCE_STYLE_GUIDE[lang_code]:
            return AUDIENCE_STYLE_GUIDE[lang_code][audience]
    return AUDIENCE_STYLE_GUIDE["en"].get(audience, "")

def get_emotionality_options(lang_code):
    return TEXTS.get(lang_code, TEXTS["en"])["emotionality_options"]

def get_complexity_options(lang_code):
    return TEXTS.get(lang_code, TEXTS["en"])["complexity_options"]

def get_speed_options(lang_code):
    return TEXTS.get(lang_code, TEXTS["en"])["speed_options"]

def get_prompt_language(lang_code):
    prompt_langs = {
        "ru": "Russian", "en": "English", "de": "German", "fr": "French",
        "es": "Spanish", "zh": "Chinese", "sq": "Albanian", "sr": "Serbian",
        "cs": "Czech", "pl": "Polish", "hu": "Hungarian"
    }
    return prompt_langs.get(lang_code, "English")

def get_structure(content_type, lang_code):
    if content_type == "business":
        structure_dict = STRUCTURES["business"]
    else:
        structure_dict = STRUCTURES["scientific"]
    if lang_code in structure_dict:
        return structure_dict[lang_code]
    return structure_dict.get("en", "")

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def call_gpt(messages, model="gpt-4o-mini", temperature=0.7):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"GPT error: {e}")
        return None

def sense_diagnosis(text, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""You are an expert in business and scientific communication. Analyze the text and return ONLY JSON.

IMPORTANT: Respond in {prompt_lang} language.

Format:
{{
  "main_thesis": "The main idea (one sentence)",
  "secondary_theses": ["thesis 1", "thesis 2"],
  "missing_thesis": "If no main thesis, what should it be?",
  "unproven_claims": ["claim without proof"],
  "hidden_meanings": ["hidden subtext"],
  "redundant_parts": ["redundant parts"],
  "diagnosis": "Brief conclusion"
}}

Text:
"""
    messages = [{"role": "user", "content": prompt + text}]
    result = call_gpt(messages)
    if result:
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
    try:
        return json.loads(result)
    except:
        return {"error": "JSON parse error", "raw": result}

def restructure(text, content_type, lang):
    structure = get_structure(content_type, lang)
    prompt_lang = get_prompt_language(lang)
    prompt = f"""{structure}

IMPORTANT: Respond in {prompt_lang} language.

Restructure the text according to this structure. Add short transitions. Remove fluff.
Return only the rewritten text.

Text:
"""
    messages = [{"role": "user", "content": prompt + text}]
    return call_gpt(messages)

def adjust_tone(text, audience, emotionality, complexity, speed, content_type, lang):
    prompt_lang = get_prompt_language(lang)
    style_guide = get_audience_style_guide(audience, lang)
    
    if content_type == "scientific":
        base_guidance = "This is a scientific/technical text. Maintain accuracy and authority."
    else:
        base_guidance = "This is a business text. Maintain persuasiveness and clarity."
    
    prompt = f"""{base_guidance}

AUDIENCE: {audience}
STYLE GUIDE FOR THIS AUDIENCE: {style_guide}

Adjust the text according to:
- Tone: match the audience's expectations
- Emotionality: {emotionality}
- Complexity: {complexity}
- Pacing: {speed}

IMPORTANT: Respond in {prompt_lang} language.

Keep the core meaning. Adapt style, vocabulary, arguments, and examples to resonate with the specified audience.
Return only the rewritten text.

Text:
"""
    messages = [{"role": "user", "content": prompt + text}]
    return call_gpt(messages)

def add_engagement(text, content_type, lang):
    prompt_lang = get_prompt_language(lang)
    if content_type == "scientific":
        engagement_rules = """
Add engagement elements suitable for scientific/technical content:
- Strong, factual headline
- Clear question in first paragraph
- Break into short paragraphs
- Add subheadings
- One contrast (old understanding / new discovery)
- One concrete example or application
- **Bold** key findings
"""
    else:
        engagement_rules = """
Add engagement elements:
- Hook title
- Question in first paragraph
- Break into short paragraphs
- Add 3-4 subheadings
- One contrast ("before / now")
- One concrete example
- **Bold** key phrases
"""
    
    prompt = f"""{engagement_rules}

IMPORTANT: Respond in {prompt_lang} language.

Return final text.

Text:
"""
    messages = [{"role": "user", "content": prompt + text}]
    return call_gpt(messages)

def literary_editing(text, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""You are a professional literary editor and stylist.

Perform literary editing on the text:
1. Remove repetitions and tautology
2. Replace repeated words with synonyms
3. Improve sentence structure and flow
4. Fix clumsy or awkward phrasing
5. Ensure grammatical correctness
6. Maintain the original meaning and tone
7. Make the text more elegant and readable

IMPORTANT: Respond in {prompt_lang} language.

Return ONLY the edited text, no explanations.

Text to edit:
"""
    messages = [{"role": "user", "content": prompt + text}]
    return call_gpt(messages, temperature=0.8)

def final_check(original, rewritten, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Compare original and rewritten text. Return ONLY JSON.

IMPORTANT: Respond in {prompt_lang} language.

Format:
{{
  "is_better": true,
  "changes_summary": "what changed and why",
  "improvements": ["improvement 1", "improvement 2"],
  "score_out_of_10": 8
}}

Original:
{original}

Rewritten:
{rewritten}
"""
    messages = [{"role": "user", "content": prompt}]
    result = call_gpt(messages)
    if result:
        result = result.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.startswith("```"):
            result = result[3:]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
    try:
        return json.loads(result)
    except:
        return result

def visual_diff(original, rewritten):
    diff = difflib.HtmlDiff(wrapcolumn=80).make_file(
        original.splitlines(), rewritten.splitlines(),
        fromdesc="Original", todesc="Rewritten", context=True, numlines=2
    )
    return diff

# ==================== ОСНОВНОЙ ИНТЕРФЕЙС ====================

lang_options = list(LANGUAGES.keys())
selected_lang_name = st.sidebar.selectbox("🌐 Language / Язык", lang_options, index=0)
ui_lang_code = LANGUAGES[selected_lang_name]

st.title(get_text("title", ui_lang_code))
st.markdown(get_text("subtitle", ui_lang_code))

with st.sidebar:
    st.header(get_text("settings", ui_lang_code))
    st.markdown("---")
    
    content_type_options = CONTENT_TYPES.get(ui_lang_code, CONTENT_TYPES["en"])
    selected_content_type_name = st.selectbox(
        get_text("content_type", ui_lang_code),
        content_type_options,
        index=0
    )
    if "Коммерческие" in selected_content_type_name or "Business" in selected_content_type_name or "Geschäfts" in selected_content_type_name:
        content_type = "business"
    else:
        content_type = "scientific"
    
    st.markdown("---")
    
    # Выбор аудитории с расширенными вариантами
    audience_options = get_audience_options(content_type, ui_lang_code)
    audience = st.selectbox(
        get_text("audience", ui_lang_code),
        audience_options,
        index=0
    )
    
    st.markdown("---")
    st.subheader(get_text("tone_params", ui_lang_code))
    
    emotionality_options = get_emotionality_options(ui_lang_code)
    emotionality = st.select_slider(
        get_text("emotionality", ui_lang_code),
        options=emotionality_options,
        value=emotionality_options[1]
    )
    
    complexity_options = get_complexity_options(ui_lang_code)
    complexity = st.select_slider(
        get_text("complexity", ui_lang_code),
        options=complexity_options,
        value=complexity_options[1]
    )
    
    speed_options = get_speed_options(ui_lang_code)
    speed = st.select_slider(
        get_text("speed", ui_lang_code),
        options=speed_options,
        value=speed_options[0]
    )
    
    st.markdown("---")
    enable_editing = st.checkbox(
        get_text("literary_editing", ui_lang_code),
        value=True,
        help=get_text("literary_editing_help", ui_lang_code)
    )
    
    st.markdown("---")
    st.caption("ReText v0.7 - Extended audiences with style guides")

input_text = st.text_area(
    get_text("text_input_label", ui_lang_code),
    height=300,
    max_chars=8000
)

if st.button(get_text("run_button", ui_lang_code)):
    if not input_text.strip():
        st.warning(get_text("warning_empty", ui_lang_code))
    else:
        target_lang = ui_lang_code
        
        with st.spinner(get_text("spinner1", ui_lang_code)):
            diagnosis = sense_diagnosis(input_text, target_lang)
        
        st.subheader(get_text("diagnosis_title", ui_lang_code))
        if "error" in diagnosis:
            st.json(diagnosis)
        else:
            st.write(f"{get_text('main_thesis', ui_lang_code)} {diagnosis.get('main_thesis', '—')}")
            st.write(f"{get_text('diagnosis', ui_lang_code)} {diagnosis.get('diagnosis', '—')}")
            if diagnosis.get("redundant_parts"):
                st.write(f"{get_text('redundant_parts', ui_lang_code)} " + ", ".join(diagnosis["redundant_parts"]))
        
        corrected_main_thesis = st.text_input(
            get_text("correct_thesis", ui_lang_code),
            value=diagnosis.get("main_thesis", "")
        )
        if corrected_main_thesis and corrected_main_thesis != diagnosis.get("main_thesis"):
            st.info(f"{get_text('using_thesis', ui_lang_code)} {corrected_main_thesis}")
        
        with st.spinner(get_text("spinner2", ui_lang_code)):
            restructured = restructure(input_text, content_type, target_lang)
        
        with st.spinner(get_text("spinner3", ui_lang_code)):
            toned = adjust_tone(restructured, audience, emotionality, complexity, speed, content_type, target_lang)
        
        with st.spinner(get_text("spinner4", ui_lang_code)):
            engaged = add_engagement(toned, content_type, target_lang)
        
        if enable_editing:
            with st.spinner(get_text("spinner5", ui_lang_code)):
                final_text = literary_editing(engaged, target_lang)
        else:
            final_text = engaged
        
        with st.spinner(get_text("spinner6", ui_lang_code)):
            report = final_check(input_text, final_text, target_lang)
        
        st.success(get_text("success", ui_lang_code))
        tab1, tab2, tab3, tab4 = st.tabs([
            get_text("tab_result", ui_lang_code),
            get_text("tab_report", ui_lang_code),
            get_text("tab_diff", ui_lang_code),
            get_text("tab_original", ui_lang_code)
        ])
        
        with tab1:
            st.markdown(final_text)
        with tab2:
            if isinstance(report, dict):
                st.json(report)
            else:
                st.write(report)
        with tab3:
            diff_html = visual_diff(input_text, final_text)
            st.components.v1.html(diff_html, height=500)
        with tab4:
            st.text(input_text)

if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1
st.sidebar.markdown(f"{get_text('session_count', ui_lang_code)} {st.session_state.visit_count}")
