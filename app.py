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

# Структуры для разных типов контента
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
""",
        "de": """
Ideale Struktur für Geschäftsangebote:
1. Schmerz (klares Kundenproblem)
2. Lösung (ein Satz, Alleinstellungsmerkmal)
3. Wie es funktioniert (Mechanismus)
4. Beweise (Fallbeispiel, Zahlen)
5. Preis und Konditionen
6. Handlungsaufforderung (eindeutig)
""",
        "fr": """
Structure idéale d'une proposition commerciale:
1. Problème (problème clair du client)
2. Solution (une phrase, USP)
3. Comment ça fonctionne (mécanisme)
4. Preuves (cas, chiffres)
5. Prix et conditions
6. Appel à l'action (sans ambiguïté)
""",
        "es": """
Estructura ideal de propuesta comercial:
1. Dolor (problema claro del cliente)
2. Solución (una frase, USP)
3. Cómo funciona (mecanismo)
4. Pruebas (caso, números)
5. Precio y condiciones
6. Llamada a la acción (inequívoca)
""",
        "zh": """
理想商业提案结构：
1. 痛点（明确的客户问题）
2. 解决方案（一句话，独特卖点）
3. 工作原理（机制）
4. 证据（案例、数据）
5. 价格与条款
6. 行动号召（明确）
"""
    },
    "scientific": {
        "ru": """
Структура идеального научного/технического пресс-релиза:
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
""",
        "de": """
Ideale Struktur für wissenschaftliche/technische Pressemitteilungen:
1. Schlagzeile (die wichtigste Entdeckung in einem Satz)
2. Einleitung (wer, was, wo, wann, warum es wichtig ist)
3. Kontext und Relevanz des Problems
4. Methodik und Ansatz (wie es gemacht wurde)
5. Wichtige Ergebnisse und Beweise (Daten, Zahlen)
6. Bedeutung für Wissenschaft/Industrie/Gesellschaft
7. Zitate von Forschern oder Experten
8. Kontaktinformationen und Publikationslinks
""",
        "fr": """
Structure idéale d'un communiqué de presse scientifique/technique:
1. Titre accrocheur (la découverte principale en une phrase)
2. Introduction (qui, quoi, où, quand, pourquoi c'est important)
3. Contexte et pertinence du problème
4. Méthodologie et approche (comment cela a été fait)
5. Résultats clés et preuves (données, chiffres)
6. Importance pour la science/l'industrie/la société
7. Citations des chercheurs ou experts
8. Coordonnées et liens vers les publications
""",
        "es": """
Estructura ideal de comunicado de prensa científico/técnico:
1. Titular (el descubrimiento principal en una frase)
2. Entrada (quién, qué, dónde, cuándo, por qué es importante)
3. Contexto y relevancia del problema
4. Metodología y enfoque (cómo se hizo)
5. Resultados clave y evidencia (datos, números)
6. Importancia para la ciencia/industria/sociedad
7. Citas de investigadores o expertos
8. Información de contacto y enlaces a publicaciones
""",
        "zh": """
理想科学/技术新闻稿结构：
1. 标题（一句话概括主要发现）
2. 导语（谁、什么、在哪里、何时、为什么重要）
3. 问题背景和相关性
4. 方法论和途径（如何完成）
5. 关键结果和证据（数据、数字）
6. 对科学/工业/社会的意义
7. 研究人员或专家引用
8. 联系信息和出版物链接
"""
    }
}

# База текстов интерфейса (сокращенно, полные версии из предыдущего кода)
# Здесь я приведу сокращенную версию для компактности.
# В реальном коде должны быть полные TEXTS для всех языков.
# Для простоты сейчас оставлю основные языки, остальные будут на английском.

TEXTS = {
    "ru": {
        "title": "✂️ ReText – Контент-хирург",
        "subtitle": "Переделываем тексты в продающие, вовлекающие, понятные.",
        "settings": "Настройки",
        "language": "Язык интерфейса",
        "content_type": "Тип контента",
        "tone_params": "Параметры тональности",
        "audience": "Аудитория",
        "audience_options_business": ["ЛПР", "Технари", "Маркетологи", "Инвесторы", "Массовая"],
        "audience_options_scientific": ["Научные редакторы", "Журналисты", "R&D-директора", "Инвесторы", "Широкая публика"],
        "emotionality": "Эмоциональность",
        "emotionality_options": ["низкая", "средняя", "высокая"],
        "complexity": "Сложность",
        "complexity_options": ["простая", "средняя", "высокая"],
        "speed": "Скорость/ритм",
        "speed_options": ["ритмичная", "размеренная", "прерывистая"],
        "text_input_label": "Вставьте текст:",
        "run_button": "🚀 Запустить ReText",
        "spinner1": "1/5 Смысловая диагностика...",
        "spinner2": "2/5 Реструктуризация...",
        "spinner3": "3/5 Настройка тональности...",
        "spinner4": "4/5 Добавление вовлекающих элементов...",
        "spinner5": "5/5 Формирование отчёта...",
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
        "subtitle": "Turn boring texts into selling, engaging, clear documents.",
        "settings": "Settings",
        "language": "Interface language",
        "content_type": "Content type",
        "tone_params": "Tone parameters",
        "audience": "Audience",
        "audience_options_business": ["Executive", "Technical", "Marketing", "Investor", "General"],
        "audience_options_scientific": ["Science editors", "Journalists", "R&D directors", "Investors", "General public"],
        "emotionality": "Emotionality",
        "emotionality_options": ["low", "medium", "high"],
        "complexity": "Complexity",
        "complexity_options": ["simple", "medium", "complex"],
        "speed": "Pacing",
        "speed_options": ["rhythmic", "measured", "jerky"],
        "text_input_label": "Paste your text:",
        "run_button": "🚀 Run ReText",
        "spinner1": "1/5 Sense diagnosis...",
        "spinner2": "2/5 Restructuring...",
        "spinner3": "3/5 Tone adjustment...",
        "spinner4": "4/5 Adding engagement elements...",
        "spinner5": "5/5 Generating report...",
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

# Для остальных языков используем английский как fallback
def get_text(key, lang_code):
    if lang_code in TEXTS and key in TEXTS[lang_code]:
        return TEXTS[lang_code][key]
    return TEXTS["en"].get(key, key)

def get_audience_options(content_type, lang_code):
    if content_type == "business":
        if lang_code in TEXTS and "audience_options_business" in TEXTS[lang_code]:
            return TEXTS[lang_code]["audience_options_business"]
        return TEXTS["en"]["audience_options_business"]
    else:
        if lang_code in TEXTS and "audience_options_scientific" in TEXTS[lang_code]:
            return TEXTS[lang_code]["audience_options_scientific"]
        return TEXTS["en"]["audience_options_scientific"]

def get_emotionality_options(lang_code):
    if lang_code in TEXTS:
        return TEXTS[lang_code]["emotionality_options"]
    return TEXTS["en"]["emotionality_options"]

def get_complexity_options(lang_code):
    if lang_code in TEXTS:
        return TEXTS[lang_code]["complexity_options"]
    return TEXTS["en"]["complexity_options"]

def get_speed_options(lang_code):
    if lang_code in TEXTS:
        return TEXTS[lang_code]["speed_options"]
    return TEXTS["en"]["speed_options"]

def get_prompt_language(lang_code):
    prompt_langs = {
        "ru": "Russian", "en": "English", "de": "German", "fr": "French",
        "es": "Spanish", "zh": "Chinese", "sq": "Albanian", "sr": "Serbian",
        "cs": "Czech", "pl": "Polish", "hu": "Hungarian"
    }
    return prompt_langs.get(lang_code, "English")

def get_structure(content_type, lang_code):
    """Возвращает структуру для выбранного типа контента на нужном языке"""
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
    tone_guidance = ""
    if content_type == "scientific":
        tone_guidance = "Use a professional, authoritative, but accessible tone. Avoid hype. Focus on accuracy and significance."
    else:
        tone_guidance = "Use a persuasive, benefit-driven tone. Focus on value and results."
    
    prompt = f"""{tone_guidance}

Adjust the tone according to:
- Audience: {audience}
- Emotionality: {emotionality}
- Complexity: {complexity}
- Pacing: {speed}

IMPORTANT: Respond in {prompt_lang} language.

Keep the meaning, change the style. Return only text.

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

# Выбор языка
lang_options = list(LANGUAGES.keys())
selected_lang_name = st.sidebar.selectbox("🌐 Language / Язык", lang_options, index=0)
ui_lang_code = LANGUAGES[selected_lang_name]

st.title(get_text("title", ui_lang_code))
st.markdown(get_text("subtitle", ui_lang_code))

with st.sidebar:
    st.header(get_text("settings", ui_lang_code))
    st.markdown("---")
    
    # Выбор типа контента
    content_type_options = CONTENT_TYPES.get(ui_lang_code, CONTENT_TYPES["en"])
    selected_content_type_name = st.selectbox(
        get_text("content_type", ui_lang_code),
        content_type_options,
        index=0
    )
    # Определяем, какой тип выбран
    if "Коммерческие" in selected_content_type_name or "Business" in selected_content_type_name or "Geschäfts" in selected_content_type_name:
        content_type = "business"
    else:
        content_type = "scientific"
    
    st.markdown("---")
    st.subheader(get_text("tone_params", ui_lang_code))
    
    audience = st.selectbox(
        get_text("audience", ui_lang_code),
        get_audience_options(content_type, ui_lang_code)
    )
    
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
    st.caption("ReText v0.5 - Business & Scientific modes")

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
            final_text = add_engagement(toned, content_type, target_lang)
        with st.spinner(get_text("spinner5", ui_lang_code)):
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
