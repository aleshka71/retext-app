import streamlit as st
import openai
import json
import difflib
from datetime import datetime
import os
import io
import re
import hashlib
import time

st.set_page_config(page_title="ReText – Editorial AI Assistant", page_icon="✂️", layout="wide")

# ==================== НАСТРОЙКИ БЕЛОЙ МАРКИРОВКИ ====================
BRAND_CONFIG = {
    "logo_emoji": "✂️",
    "app_name": "ReText",
    "company_name": "TEXTUM",
    "primary_color": "#FF4B4B",
    "secondary_color": "#1E88E5",
    "custom_css": """
        .stApp { background-color: #fafafa; }
        .stButton button { background-color: #FF4B4B; color: white; border-radius: 8px; }
        .stButton button:hover { background-color: #e03e3e; }
    """
}

st.markdown(f"<style>{BRAND_CONFIG['custom_css']}</style>", unsafe_allow_html=True)

# ==================== АВТОРИЗАЦИЯ ====================
PASSWORD = "retext2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        pwd = st.text_input(f"🔐 {BRAND_CONFIG['app_name']} – enter password:", type="password")
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("Invalid password")
        st.stop()

check_password()

# ==================== ПОДПИСКА И ЛИМИТЫ ====================
if "usage_count" not in st.session_state:
    st.session_state.usage_count = 0
if "subscription_tier" not in st.session_state:
    st.session_state.subscription_tier = "free"

def check_usage_limit():
    limits = {"free": 5, "pro": 100, "business": 1000}
    limit = limits.get(st.session_state.subscription_tier, 5)
    if st.session_state.usage_count >= limit and st.session_state.subscription_tier == "free":
        st.warning("⚠️ Free limit (5 uses) reached. Upgrade in settings.")
        return False
    return True

def increment_usage():
    st.session_state.usage_count += 1

# ==================== ИСТОРИЯ ОБРАБОТКИ ====================
if "history" not in st.session_state:
    st.session_state.history = []

def add_to_history(original, result):
    st.session_state.history.insert(0, {"original": original[:500], "result": result[:500], "timestamp": datetime.now().isoformat()})
    st.session_state.history = st.session_state.history[:10]

# ==================== ГЛОССАРИЙ ТЕРМИНОВ ====================
if "glossary" not in st.session_state:
    st.session_state.glossary = {}

def apply_glossary(text):
    for term, replacement in st.session_state.glossary.items():
        text = re.sub(rf'\b{re.escape(term)}\b', replacement, text, flags=re.IGNORECASE)
    return text

# ==================== МНОГОЯЗЫЧНЫЙ ИНТЕРФЕЙС ====================
LANGUAGES = {
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
    "🇩🇪 Deutsch": "de",
    "🇫🇷 Français": "fr",
    "🇪🇸 Español": "es",
    "🇷🇸 Srpski": "sr",
    "🇦🇱 Shqip": "sq",
    "🇵🇱 Polski": "pl",
    "🇭🇺 Magyar": "hu",
    "🇨🇿 Čeština": "cs"
}

# Опции для слайдеров (для каждого языка)
OPTIONS = {
    "ru": {
        "emotionality": ["низкая", "средняя", "высокая"],
        "complexity": ["простая", "средняя", "высокая"],
        "speed": ["ритмичная", "размеренная", "прерывистая"]
    },
    "en": {
        "emotionality": ["low", "medium", "high"],
        "complexity": ["simple", "medium", "complex"],
        "speed": ["rhythmic", "measured", "jerky"]
    },
    "de": {
        "emotionality": ["niedrig", "mittel", "hoch"],
        "complexity": ["einfach", "mittel", "komplex"],
        "speed": ["rhythmisch", "gemäßigt", "ruckartig"]
    },
    "fr": {
        "emotionality": ["faible", "moyenne", "élevée"],
        "complexity": ["simple", "moyenne", "complexe"],
        "speed": ["rythmé", "mesuré", "saccadé"]
    },
    "es": {
        "emotionality": ["baja", "media", "alta"],
        "complexity": ["simple", "media", "compleja"],
        "speed": ["rítmico", "pausado", "entrecortado"]
    },
    "sr": {
        "emotionality": ["niska", "srednja", "visoka"],
        "complexity": ["jednostavna", "srednja", "složena"],
        "speed": ["ritmičan", "odmeren", "isprekidan"]
    },
    "sq": {
        "emotionality": ["i ulët", "i mesëm", "i lartë"],
        "complexity": ["i thjeshtë", "i mesëm", "kompleks"],
        "speed": ["ritmik", "i matur", "i ndërprerë"]
    },
    "pl": {
        "emotionality": ["niska", "średnia", "wysoka"],
        "complexity": ["prosta", "średnia", "złożona"],
        "speed": ["rytmiczny", "wyważony", "urywany"]
    },
    "hu": {
        "emotionality": ["alacsony", "közepes", "magas"],
        "complexity": ["egyszerű", "közepes", "összetett"],
        "speed": ["ritmikus", "mértéktartó", "szaggatott"]
    },
    "cs": {
        "emotionality": ["nízká", "střední", "vysoká"],
        "complexity": ["jednoduchá", "střední", "složitá"],
        "speed": ["rytmický", "odměřený", "trhavý"]
    }
}

# Тексты интерфейса
TEXTS = {
    "ru": {
        "title": f"{BRAND_CONFIG['logo_emoji']} {BRAND_CONFIG['app_name']} – Редакционный ИИ-ассистент",
        "subtitle": "Расшифровка интервью, анализ документов, SEO, HR, выступления, фактчекинг, юр. проверка.",
        "settings": "Настройки", "language": "Язык интерфейса", "assistant": "Ассистент",
        "styleguide": "📚 Стайлгайд издания", "examples": "📁 Примеры и референсы",
        "glossary": "📖 Глоссарий терминов", "google_docs": "🔗 Google Docs",
        "google_docs_url": "Ссылка на Google Doc", "google_docs_import": "📥 Импортировать",
        "google_docs_export": "📤 Экспорт", "audience": "Аудитория и задача",
        "emotionality": "Эмоциональность", "complexity": "Сложность", "speed": "Скорость/ритм",
        "text_input_label": "Вставьте текст:", "run_button": "🚀 Запустить",
        "spinner1": "1/9 Диагностика...", "spinner2": "2/9 Структура...", "spinner3": "3/9 Тон...",
        "spinner4": "4/9 Вовлечение...", "spinner5": "5/9 Редактура...", "spinner6": "6/9 Проверка...",
        "spinner7": "7/9 Фактчекинг...", "spinner8": "8/9 Глоссарий...", "spinner9": "9/9 Отчёт...",
        "diagnosis_title": "🔍 Диагностика", "main_thesis": "**Главная мысль:**", "diagnosis": "**Диагноз:**",
        "redundant_parts": "**Лишние части:**", "correct_thesis": "Исправьте:", "using_thesis": "Используем:",
        "success": "Готово!", "tab_result": "📄 Результат", "tab_report": "📊 Отчёт",
        "tab_diff": "🔍 Сравнение", "tab_original": "📜 Исходный", "tab_verification": "🔍 Верификация",
        "tab_history": "📜 История", "session_count": "Сессий:", "warning_empty": "Введите текст",
        "verification_header": "Протокол", "verification_checklist": "**Проверить:**",
        "verification_assumptions": "**⚠️ Предположения:**", "verification_ready": "**✅ Готово:**",
        "factcheck_found": "**🔍 Факты для проверки:**", "legal_risks": "**⚖️ Юр. риски:**",
        "export_to_docs": "📋 Скопировать", "subscription": "Тариф",
        "subscription_free": "Бесплатный (5)", "subscription_pro": "Pro (100)", "subscription_business": "Business (1000)",
        "usage_left": "Осталось:", "upgrade_button": "💳 Обновить",
        "google_docs_import_success": "Импортировано", "google_docs_error": "Ошибка импорта"
    },
    "en": {
        "title": f"{BRAND_CONFIG['logo_emoji']} {BRAND_CONFIG['app_name']} – Editorial AI Assistant",
        "subtitle": "Interview transcription, document analysis, SEO, HR, speeches, fact-checking, legal review.",
        "settings": "Settings", "language": "Interface language", "assistant": "Assistant",
        "styleguide": "📚 Style guide", "examples": "📁 Examples & references",
        "glossary": "📖 Glossary", "google_docs": "🔗 Google Docs",
        "google_docs_url": "Google Doc URL", "google_docs_import": "📥 Import",
        "google_docs_export": "📤 Export", "audience": "Audience & task",
        "emotionality": "Emotionality", "complexity": "Complexity", "speed": "Pacing",
        "text_input_label": "Paste text:", "run_button": "🚀 Run",
        "spinner1": "1/9 Diagnosis...", "spinner2": "2/9 Structure...", "spinner3": "3/9 Tone...",
        "spinner4": "4/9 Engagement...", "spinner5": "5/9 Editing...", "spinner6": "6/9 Check...",
        "spinner7": "7/9 Fact-check...", "spinner8": "8/9 Glossary...", "spinner9": "9/9 Report...",
        "diagnosis_title": "🔍 Diagnosis", "main_thesis": "**Main thesis:**", "diagnosis": "**Diagnosis:**",
        "redundant_parts": "**Redundant:**", "correct_thesis": "Correct:", "using_thesis": "Using:",
        "success": "Done!", "tab_result": "📄 Result", "tab_report": "📊 Report",
        "tab_diff": "🔍 Compare", "tab_original": "📜 Original", "tab_verification": "🔍 Verify",
        "tab_history": "📜 History", "session_count": "Sessions:", "warning_empty": "Enter text",
        "verification_header": "Protocol", "verification_checklist": "**Verify:**",
        "verification_assumptions": "**⚠️ Assumptions:**", "verification_ready": "**✅ Ready:**",
        "factcheck_found": "**🔍 Facts to verify:**", "legal_risks": "**⚖️ Legal risks:**",
        "export_to_docs": "📋 Copy", "subscription": "Plan",
        "subscription_free": "Free (5)", "subscription_pro": "Pro (100)", "subscription_business": "Business (1000)",
        "usage_left": "Left:", "upgrade_button": "💳 Upgrade",
        "google_docs_import_success": "Imported", "google_docs_error": "Import failed"
    }
}

# Функции для получения текста и опций
def get_text(key, lang):
    if lang in TEXTS:
        return TEXTS[lang].get(key, TEXTS["en"].get(key, key))
    return TEXTS["en"].get(key, key)

def get_options(lang, option_type):
    """Возвращает опции для слайдера на нужном языке"""
    if lang in OPTIONS and option_type in OPTIONS[lang]:
        return OPTIONS[lang][option_type]
    return OPTIONS["en"][option_type]

def get_prompt_language(lang):
    prompt_langs = {
        "ru": "Russian", "en": "English", "de": "German", "fr": "French",
        "es": "Spanish", "sr": "Serbian", "sq": "Albanian", "pl": "Polish",
        "hu": "Hungarian", "cs": "Czech"
    }
    return prompt_langs.get(lang, "English")

def extract_text_from_uploaded(file):
    if file is None:
        return ""
    content = file.read()
    if file.type == "text/plain":
        return content.decode("utf-8")
    elif "pdf" in file.type:
        try:
            import PyPDF2
            pdf = PyPDF2.PdfReader(io.BytesIO(content))
            return "\n".join([page.extract_text() for page in pdf.pages])
        except:
            return "[PDF read error]"
    elif "word" in file.type or "document" in file.type:
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            return "[DOCX read error]"
    return ""

def import_from_google_docs(url):
    try:
        doc_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if not doc_id_match:
            return None
        doc_id = doc_id_match.group(1)
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        import requests
        resp = requests.get(export_url, timeout=10)
        if resp.status_code == 200:
            return resp.text
        return None
    except:
        return None

# ==================== БИБЛИОТЕКА АССИСТЕНТОВ ====================
def get_assistants(lang):
    base = {
        "business_proposal": {"icon": "📄", "name_ru": "Коммерческие предложения (B2B)", "name_en": "Business Proposals (B2B)"},
        "scientific": {"icon": "🔬", "name_ru": "Научные/технические пресс-релизы", "name_en": "Scientific/Technical Press Releases"},
        "interview": {"icon": "🎙️", "name_ru": "Расшифровка интервью → черновик", "name_en": "Interview transcript → draft"},
        "document_analysis": {"icon": "📑", "name_ru": "Анализ документа (отчёт, закон)", "name_en": "Document analysis"},
        "seo": {"icon": "📈", "name_ru": "SEO-упаковка и адаптация", "name_en": "SEO packaging"},
        "speech": {"icon": "🎤", "name_ru": "Выступление / Доклад на конференции", "name_en": "Speech / Conference talk"},
        "vacancy": {"icon": "💼", "name_ru": "Вакансия / Оффер (HR)", "name_en": "Job vacancy / Offer (HR)"}
    }
    result = []
    for key, data in base.items():
        name = data.get(f"name_{lang}", data.get("name_en", data["name_ru"]))
        result.append({
            "id": key,
            "name": f"{data['icon']} {name}",
            "icon": data["icon"],
            "description": "",
            "structure": "",
            "system_prompt": ""
        })
    return result

# ==================== АУДИТОРНЫЕ ГРУППЫ ====================
AUDIENCE_OPTIONS = {
    "ru": ["👔 ЛПР", "⚙️ Технари", "📢 Маркетологи", "💰 Инвесторы", "👥 Массовая", "🎯 Сотрудники", "🏢 B2B", "🛍️ B2C"],
    "en": ["👔 Executive", "⚙️ Technical", "📢 Marketing", "💰 Investor", "👥 General", "🎯 Employees", "🏢 B2B", "🛍️ B2C"],
    "de": ["👔 Führung", "⚙️ Technik", "📢 Marketing", "💰 Investor", "👥 Öffentlichkeit", "🎯 Mitarbeiter", "🏢 B2B", "🛍️ B2C"],
    "fr": ["👔 Dirigeant", "⚙️ Technique", "📢 Marketing", "💰 Investisseur", "👥 Public", "🎯 Employés", "🏢 B2B", "🛍️ B2C"],
    "es": ["👔 Ejecutivo", "⚙️ Técnico", "📢 Marketing", "💰 Inversor", "👥 Público", "🎯 Empleados", "🏢 B2B", "🛍️ B2C"],
    "sr": ["👔 Rukovodilac", "⚙️ Tehničari", "📢 Marketing", "💰 Investitori", "👥 Publika", "🎯 Zaposleni", "🏢 B2B", "🛍️ B2C"],
    "sq": ["👔 Ekzekutiv", "⚙️ Teknik", "📢 Marketing", "💰 Investitor", "👥 Publiku", "🎯 Punonjës", "🏢 B2B", "🛍️ B2C"],
    "pl": ["👔 Kierownictwo", "⚙️ Technicy", "📢 Marketing", "💰 Inwestorzy", "👥 Publiczność", "🎯 Pracownicy", "🏢 B2B", "🛍️ B2C"],
    "hu": ["👔 Vezető", "⚙️ Műszaki", "📢 Marketing", "💰 Befektető", "👥 Közönség", "🎯 Alkalmazottak", "🏢 B2B", "🛍️ B2C"],
    "cs": ["👔 Vedení", "⚙️ Technici", "📢 Marketing", "💰 Investoři", "👥 Veřejnost", "🎯 Zaměstnanci", "🏢 B2B", "🛍️ B2C"]
}

def get_audience_options(lang):
    return AUDIENCE_OPTIONS.get(lang, AUDIENCE_OPTIONS["en"])

# ==================== ФУНКЦИИ ДЛЯ ФАКТЧЕКИНГА ====================
def factcheck_and_legal(text, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Analyze the text for:
1. FACT-CHECKING: Identify factual claims that need verification. Return as list.
2. LEGAL RISKS: Identify phrases that may pose legal risks. Return as list.

Return ONLY JSON:
{{
  "facts_to_verify": [],
  "legal_risks": []
}}

IMPORTANT: Respond in {prompt_lang} language.

Text: {text[:3000]}
"""
    messages = [{"role": "user", "content": prompt}]
    result = call_gpt(messages, temperature=0.5)
    if result:
        result = result.strip()
        for prefix in ["```json", "```"]:
            if result.startswith(prefix):
                result = result[len(prefix):]
        if result.endswith("```"):
            result = result[:-3]
        result = result.strip()
    try:
        return json.loads(result)
    except:
        return {"facts_to_verify": [], "legal_risks": []}

# ==================== ОСНОВНЫЕ АГЕНТЫ ====================
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
    prompt = f"""Analyze text, return ONLY JSON.
{{
  "main_thesis": "...",
  "secondary_theses": [],
  "missing_thesis": "",
  "unproven_claims": [],
  "hidden_meanings": [],
  "redundant_parts": [],
  "diagnosis": ""
}}
Respond in {prompt_lang}.
Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    result = call_gpt(messages)
    if result:
        result = re.sub(r'^```json\s*', '', result)
        result = re.sub(r'```$', '', result)
        result = result.strip()
    try:
        return json.loads(result)
    except:
        return {"error": "JSON parse", "raw": result}

def restructure(text, assistant, lang, styleguide="", examples="", glossary=""):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Assistant: {assistant.get('name','')}
Style guide: {styleguide[:2000]}
Examples: {examples[:2000]}
Glossary: {glossary[:1000]}

Restructure text according to best practices.
Rules:
- No tiny headings, merge short blocks
- No "this is not just...", no pleonasms
- Each paragraph = one thought, smooth transitions
- If vacancy: focus on benefits, culture, growth
- If speech: start with pain/benefit, end with call to action

Respond in {prompt_lang}. Return only restructured text.

Text: {text[:4000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages)

def adjust_tone(text, audience, emotionality, complexity, speed, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Adjust tone for: {audience}
Emotionality: {emotionality}, Complexity: {complexity}, Pacing: {speed}
Rules: answer "Why relevant?", "How connected?", "What to do?"
Return only text.

Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages)

def add_engagement(text, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Add hook title, question in first paragraph, short paragraphs, subheadings only if helpful, one contrast, one example, bold key phrases. No tiny headings. Return text.
Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages)

def literary_editing(text, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Literary editing: remove repetitions, tautology, forbidden constructions, pleonasms, empty phrases, clichés. Group homogeneous items. Return text.
Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages, temperature=0.8)

def final_checklist(text, lang, assistant_name):
    prompt_lang = get_prompt_language(lang)
    extra = ""
    if "speech" in assistant_name.lower() or "выступление" in assistant_name.lower():
        extra = "Ensure: starts with pain/benefit, has clear call to action, avoids 'you should' without benefit."
    if "vacancy" in assistant_name.lower() or "вакансия" in assistant_name.lower():
        extra = "Ensure: benefits, culture, growth, clear next step."
    prompt = f"""Fix issues: no tiny headings, forbidden constructions, pleonasms, empty phrases, repetitions, clichés. {extra} Return corrected text.
Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages, temperature=0.5)

def generate_verification_report(text, original, lang):
    stop_phrases = {
        "ru": ["как бы", "наверное", "может быть", "я не знаю", "вы должны", "вы ошибаетесь", "часто", "некоторые", "многие", "заявочку", "договорчик", "сделаем всё", "свяжемся как только сможем", "звоните в любое время"],
        "en": ["kind of", "maybe", "perhaps", "i don't know", "you must", "you are wrong", "some", "many", "probably"]
    }
    found_stop = [p for p in stop_phrases.get(lang, stop_phrases["en"]) if p in text.lower()]
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Generate verification JSON:
{{
  "must_verify": [],
  "assumptions": [],
  "ready_to_use": [],
  "overall_verdict": "ready with caution"
}}
Respond in {prompt_lang}.
Original: {original[:1500]}
Rewritten: {text[:1500]}"""
    messages = [{"role": "user", "content": prompt}]
    result = call_gpt(messages, temperature=0.5)
    try:
        verif = json.loads(re.sub(r'```json\s*|```', '', result).strip())
    except:
        verif = {"must_verify": [], "assumptions": [], "ready_to_use": [], "overall_verdict": "needs revision"}
    verif["stop_phrases_found"] = found_stop
    return verif

def final_check(original, rewritten, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Compare original and rewritten. Return JSON: {{"is_better": true, "changes_summary": "", "improvements": [], "score_out_of_10": 8}} in {prompt_lang}.
Original: {original[:1500]}
Rewritten: {rewritten[:1500]}"""
    messages = [{"role": "user", "content": prompt}]
    result = call_gpt(messages)
    try:
        return json.loads(re.sub(r'```json\s*|```', '', result).strip())
    except:
        return {"is_better": True, "changes_summary": "Text restructured", "improvements": ["Style", "Structure"], "score_out_of_10": 7}

def visual_diff(original, rewritten):
    diff = difflib.HtmlDiff(wrapcolumn=80).make_file(
        original.splitlines(), rewritten.splitlines(),
        fromdesc="Original", todesc="Rewritten", context=True, numlines=2
    )
    return diff

# ==================== ОСНОВНОЙ ИНТЕРФЕЙС ====================
for key in ["styleguide_content", "examples_list", "input_text", "last_result"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "examples_list" else []

lang_options = list(LANGUAGES.keys())
selected_lang_name = st.sidebar.selectbox("🌐 Language / Язык", lang_options, index=0)
ui_lang = LANGUAGES[selected_lang_name]

st.title(get_text("title", ui_lang))
st.markdown(get_text("subtitle", ui_lang))

with st.sidebar:
    st.header(get_text("settings", ui_lang))
    st.markdown("---")
    
    st.subheader(get_text("subscription", ui_lang))
    tier = st.selectbox("", [get_text("subscription_free", ui_lang), get_text("subscription_pro", ui_lang), get_text("subscription_business", ui_lang)], index=0)
    if tier == get_text("subscription_free", ui_lang):
        st.session_state.subscription_tier = "free"
    elif tier == get_text("subscription_pro", ui_lang):
        st.session_state.subscription_tier = "pro"
    else:
        st.session_state.subscription_tier = "business"
    
    remaining = 5 - st.session_state.usage_count if st.session_state.subscription_tier == "free" else "unlimited"
    st.caption(f"{get_text('usage_left', ui_lang)} {remaining}")
    if st.button(get_text("upgrade_button", ui_lang)):
        st.session_state.subscription_tier = "pro"
        st.rerun()
    
    st.markdown("---")
    assistants = get_assistants(ui_lang)
    assistant_names = [a["name"] for a in assistants]
    selected_assistant_name = st.selectbox(get_text("assistant", ui_lang), assistant_names, index=0)
    selected_assistant = next(a for a in assistants if a["name"] == selected_assistant_name)
    
    st.markdown("---")
    uploaded_styleguide = st.file_uploader(get_text("styleguide", ui_lang), type=["txt","pdf","docx"])
    if uploaded_styleguide:
        txt = extract_text_from_uploaded(uploaded_styleguide)
        if txt and not txt.startswith("["):
            st.session_state.styleguide_content = txt
            st.success("✅")
    
    st.markdown("---")
    uploaded_examples = st.file_uploader(get_text("examples", ui_lang), type=["txt","pdf","docx"], accept_multiple_files=True)
    if uploaded_examples:
        ex_list = []
        for f in uploaded_examples:
            t = extract_text_from_uploaded(f)
            if t and not t.startswith("["):
                ex_list.append(t)
        if ex_list:
            st.session_state.examples_list = ex_list
            st.success(f"✅ {len(ex_list)}")
    
    st.markdown("---")
    st.subheader(get_text("glossary", ui_lang))
    glossary_input = st.text_area("Format: term = replacement (one per line)", height=100,
                                  placeholder="product = solution\nfast = quick")
    if st.button("Load glossary"):
        st.session_state.glossary = {}
        for line in glossary_input.strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                st.session_state.glossary[k.strip()] = v.strip()
        st.success(f"✅ {len(st.session_state.glossary)} terms")
    
    st.markdown("---")
    st.subheader(get_text("google_docs", ui_lang))
    gdocs_url = st.text_input(get_text("google_docs_url", ui_lang))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(get_text("google_docs_import", ui_lang)):
            imported = import_from_google_docs(gdocs_url)
            if imported:
                st.session_state.input_text = imported
                st.success(get_text("google_docs_import_success", ui_lang))
                st.rerun()
    with col2:
        if st.button(get_text("google_docs_export", ui_lang)):
            if st.session_state.get("last_result"):
                st.info("📋 Result copied (select and copy manually)")
    
    st.markdown("---")
    audience_options = get_audience_options(ui_lang)
    audience = st.selectbox(get_text("audience", ui_lang), audience_options, index=0)
    
    st.markdown("---")
    # Используем OPTIONS для слайдеров
    emotionality_opts = get_options(ui_lang, "emotionality")
    emotionality = st.select_slider(
        get_text("emotionality", ui_lang),
        options=emotionality_opts,
        value=emotionality_opts[1] if len(emotionality_opts) > 1 else emotionality_opts[0]
    )
    
    complexity_opts = get_options(ui_lang, "complexity")
    complexity = st.select_slider(
        get_text("complexity", ui_lang),
        options=complexity_opts,
        value=complexity_opts[1] if len(complexity_opts) > 1 else complexity_opts[0]
    )
    
    speed_opts = get_options(ui_lang, "speed")
    speed = st.select_slider(
        get_text("speed", ui_lang),
        options=speed_opts,
        value=speed_opts[0]
    )
    
    st.markdown("---")
    st.caption(f"{BRAND_CONFIG['app_name']} v2.0 – {BRAND_CONFIG['company_name']}")

input_text = st.text_area(get_text("text_input_label", ui_lang), height=250, max_chars=8000, value=st.session_state.input_text)

col1, col2, col3 = st.columns([1,2,1])
with col2:
    run = st.button(get_text("run_button", ui_lang), type="primary", use_container_width=True)

if run:
    if not input_text.strip():
        st.warning(get_text("warning_empty", ui_lang))
    elif not check_usage_limit():
        st.stop()
    else:
        increment_usage()
        target_lang = ui_lang
        examples = st.session_state.examples_list
        style = st.session_state.styleguide_content
        glossary = "\n".join([f"{k} → {v}" for k,v in st.session_state.glossary.items()])
        
        with st.spinner(get_text("spinner1", ui_lang)):
            diagnosis = sense_diagnosis(input_text, target_lang)
        st.subheader(get_text("diagnosis_title", ui_lang))
        if "error" not in diagnosis:
            st.write(f"{get_text('main_thesis', ui_lang)} {diagnosis.get('main_thesis','—')}")
            st.write(f"{get_text('diagnosis', ui_lang)} {diagnosis.get('diagnosis','—')}")
        
        with st.spinner(get_text("spinner2", ui_lang)):
            restructured = restructure(input_text, selected_assistant, target_lang, style, "\n".join(examples[:3]), glossary)
        with st.spinner(get_text("spinner3", ui_lang)):
            toned = adjust_tone(restructured, audience, emotionality, complexity, speed, target_lang)
        with st.spinner(get_text("spinner4", ui_lang)):
            engaged = add_engagement(toned, target_lang)
        with st.spinner(get_text("spinner5", ui_lang)):
            edited = literary_editing(engaged, target_lang)
        with st.spinner(get_text("spinner6", ui_lang)):
            final_text = final_checklist(edited, target_lang, selected_assistant["name"])
        
        if st.session_state.glossary:
            final_text = apply_glossary(final_text)
        
        with st.spinner(get_text("spinner7", ui_lang)):
            fact_legal = factcheck_and_legal(final_text, target_lang)
        with st.spinner(get_text("spinner8", ui_lang)):
            verification = generate_verification_report(final_text, input_text, target_lang)
        with st.spinner(get_text("spinner9", ui_lang)):
            report = final_check(input_text, final_text, target_lang)
        
        st.session_state.last_result = final_text
        add_to_history(input_text, final_text)
        st.success(get_text("success", ui_lang))
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            get_text("tab_result", ui_lang), get_text("tab_report", ui_lang),
            get_text("tab_diff", ui_lang), get_text("tab_original", ui_lang),
            get_text("tab_verification", ui_lang), get_text("tab_history", ui_lang)
        ])
        with tab1:
            st.markdown(final_text)
            st.markdown("---")
            st.caption(get_text("export_to_docs", ui_lang))
            st.code(final_text, language="markdown")
        with tab2:
            if isinstance(report, dict):
                st.metric("Quality", f"{report.get('score_out_of_10','—')}/10")
                st.write("**Improvements:**", report.get("improvements", []))
                st.write("**Changes:**", report.get("changes_summary", ""))
        with tab3:
            diff_html = visual_diff(input_text, final_text)
            st.components.v1.html(diff_html, height=500)
        with tab4:
            st.text(input_text)
        with tab5:
            st.markdown(f"### {get_text('verification_header', ui_lang)}")
            if verification.get("stop_phrases_found"):
                st.markdown("**🚫 Stop phrases:** " + ", ".join(verification["stop_phrases_found"]))
            if fact_legal.get("facts_to_verify"):
                st.markdown(get_text("factcheck_found", ui_lang))
                for f in fact_legal["facts_to_verify"]:
                    st.markdown(f"- 🔍 {f}")
            if fact_legal.get("legal_risks"):
                st.markdown(get_text("legal_risks", ui_lang))
                for r in fact_legal["legal_risks"]:
                    st.markdown(f"- ⚖️ {r}")
            if verification.get("must_verify"):
                st.markdown(get_text("verification_checklist", ui_lang))
                for v in verification["must_verify"]:
                    st.markdown(f"- [ ] {v}")
            if verification.get("assumptions"):
                st.markdown(get_text("verification_assumptions", ui_lang))
                for a in verification["assumptions"]:
                    st.markdown(f"- ⚠️ {a}")
            verdict = verification.get("overall_verdict", "needs revision")
            if verdict == "ready with caution":
                st.info("🟡 Use with caution")
            else:
                st.warning("🔴 Needs revision")
        with tab6:
            if st.session_state.history:
                for i, item in enumerate(st.session_state.history[:5]):
                    with st.expander(f"{item['timestamp'][:16]} – {item['original'][:80]}..."):
                        st.text("Original: " + item['original'])
                        st.text("Result: " + item['result'])
            else:
                st.info("No history yet")

if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1
st.sidebar.markdown(f"{get_text('session_count', ui_lang)} {st.session_state.visit_count}")
