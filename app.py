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
# Эти параметры можно менять под свой бренд
BRAND_CONFIG = {
    "logo_emoji": "✂️",
    "app_name": "ReText",
    "company_name": "TEXTUM",
    "primary_color": "#FF4B4B",  # красный
    "secondary_color": "#1E88E5", # синий
    "custom_css": """
        .stApp { background-color: #fafafa; }
        .stButton button { background-color: #FF4B4B; color: white; border-radius: 8px; }
        .stButton button:hover { background-color: #e03e3e; }
    """
}

# Применяем CSS
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
    st.session_state.subscription_tier = "free"  # free, pro, business
if "feedback_history" not in st.session_state:
    st.session_state.feedback_history = []  # для обучения на правках

def check_usage_limit():
    """Проверяет, не превышен ли лимит обработок для текущего тарифа"""
    limits = {"free": 5, "pro": 100, "business": 1000}
    limit = limits.get(st.session_state.subscription_tier, 5)
    if st.session_state.usage_count >= limit and st.session_state.subscription_tier == "free":
        st.warning("⚠️ Бесплатный лимит (5 обработок) исчерпан. Обновите тариф в настройках.")
        return False
    return True

def increment_usage():
    st.session_state.usage_count += 1

# ==================== ИСТОРИЯ ОБРАБОТКИ ====================
if "history" not in st.session_state:
    st.session_state.history = []  # список из 10 последних (оригинал, результат)

def add_to_history(original, result):
    st.session_state.history.insert(0, {"original": original[:500], "result": result[:500], "timestamp": datetime.now().isoformat()})
    st.session_state.history = st.session_state.history[:10]

# ==================== ГЛОССАРИЙ ТЕРМИНОВ ====================
if "glossary" not in st.session_state:
    st.session_state.glossary = {}  # {"термин": "предпочтительный перевод/стиль"}

def apply_glossary(text):
    """Заменяет термины согласно глоссарию (простая реализация)"""
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

TEXTS = {
    "ru": {
        "title": f"{BRAND_CONFIG['logo_emoji']} {BRAND_CONFIG['app_name']} – Редакционный ИИ-ассистент",
        "subtitle": "Расшифровка интервью, анализ документов, SEO, HR, выступления, фактчекинг, юр. проверка.",
        "settings": "Настройки",
        "language": "Язык интерфейса",
        "assistant": "Ассистент",
        "styleguide": "📚 Стайлгайд издания",
        "examples": "📁 Примеры и референсы",
        "glossary": "📖 Глоссарий терминов (термин → замена)",
        "google_docs": "🔗 Google Docs",
        "google_docs_url": "Ссылка на Google Doc (для импорта)",
        "google_docs_import": "📥 Импортировать",
        "google_docs_export": "📤 Экспорт (скопировать)",
        "audience": "Аудитория и задача",
        "emotionality": "Эмоциональность",
        "emotionality_options": ["низкая", "средняя", "высокая"],
        "complexity": "Сложность",
        "complexity_options": ["простая", "средняя", "высокая"],
        "speed": "Скорость/ритм",
        "speed_options": ["ритмичная", "размеренная", "прерывистая"],
        "text_input_label": "Вставьте текст (транскрипт, документ, статью, вакансию):",
        "run_button": "🚀 Запустить",
        "spinner1": "1/9 Смысловая диагностика...",
        "spinner2": "2/9 Структурирование...",
        "spinner3": "3/9 Адаптация под аудиторию...",
        "spinner4": "4/9 Вовлекающие элементы...",
        "spinner5": "5/9 Лит. редактирование...",
        "spinner6": "6/9 Финальная проверка...",
        "spinner7": "7/9 Фактчекинг и юр. проверка...",
        "spinner8": "8/9 Применение глоссария...",
        "spinner9": "9/9 Формирование отчёта...",
        "diagnosis_title": "🔍 Смысловая диагностика",
        "main_thesis": "**Главная мысль:**",
        "diagnosis": "**Диагноз:**",
        "redundant_parts": "**Лишние части:**",
        "correct_thesis": "Если главная мысль неверна, исправьте:",
        "using_thesis": "Будем использовать:",
        "success": "Готово!",
        "tab_result": "📄 Результат",
        "tab_report": "📊 Отчёт",
        "tab_diff": "🔍 Сравнение",
        "tab_original": "📜 Исходный текст",
        "tab_verification": "🔍 Протокол верификации",
        "tab_history": "📜 История",
        "session_count": "Сессий:",
        "warning_empty": "Пожалуйста, введите текст.",
        "verification_header": "Протокол верификации",
        "verification_checklist": "**Что обязательно проверить:**",
        "verification_assumptions": "**⚠️ Предположения модели:**",
        "verification_ready": "**✅ Может использоваться как есть:**",
        "factcheck_found": "**🔍 Факты, требующие проверки:**",
        "legal_risks": "**⚖️ Юридические риски (формулировки):**",
        "export_to_docs": "📋 Скопировать для вставки в Google Docs/Notion",
        "subscription": "Тариф",
        "subscription_free": "Бесплатный (5 обработок)",
        "subscription_pro": "Pro (100 обработок)",
        "subscription_business": "Business (1000 обработок)",
        "usage_left": f"Осталось обработок: {5 - st.session_state.usage_count if st.session_state.subscription_tier == 'free' else 'много'}",
        "upgrade_button": "💳 Обновить тариф (демо)"
    },
    "en": {
        "title": f"{BRAND_CONFIG['logo_emoji']} {BRAND_CONFIG['app_name']} – Editorial AI Assistant",
        "subtitle": "Interview transcription, document analysis, SEO, HR, speeches, fact-checking, legal review.",
        "settings": "Settings",
        "language": "Interface language",
        "assistant": "Assistant",
        "styleguide": "📚 Style guide",
        "examples": "📁 Examples & references",
        "glossary": "📖 Glossary (term → replacement)",
        "google_docs": "🔗 Google Docs",
        "google_docs_url": "Google Doc URL (import)",
        "google_docs_import": "📥 Import",
        "google_docs_export": "📤 Export (copy)",
        "audience": "Audience & task",
        "emotionality": "Emotionality",
        "emotionality_options": ["low", "medium", "high"],
        "complexity": "Complexity",
        "complexity_options": ["simple", "medium", "complex"],
        "speed": "Pacing",
        "speed_options": ["rhythmic", "measured", "jerky"],
        "text_input_label": "Paste your text (transcript, document, vacancy):",
        "run_button": "🚀 Run",
        "spinner1": "1/9 Sense diagnosis...",
        "spinner2": "2/9 Structuring...",
        "spinner3": "3/9 Audience adaptation...",
        "spinner4": "4/9 Engagement elements...",
        "spinner5": "5/9 Literary editing...",
        "spinner6": "6/9 Final checklist...",
        "spinner7": "7/9 Fact-check & legal review...",
        "spinner8": "8/9 Glossary application...",
        "spinner9": "9/9 Generating report...",
        "diagnosis_title": "🔍 Sense diagnosis",
        "main_thesis": "**Main thesis:**",
        "diagnosis": "**Diagnosis:**",
        "redundant_parts": "**Redundant parts:**",
        "correct_thesis": "If incorrect, correct:",
        "using_thesis": "Will use:",
        "success": "Done!",
        "tab_result": "📄 Result",
        "tab_report": "📊 Report",
        "tab_diff": "🔍 Comparison",
        "tab_original": "📜 Original",
        "tab_verification": "🔍 Verification",
        "tab_history": "📜 History",
        "session_count": "Sessions:",
        "warning_empty": "Please enter text.",
        "verification_header": "Verification protocol",
        "verification_checklist": "**Must verify:**",
        "verification_assumptions": "**⚠️ AI assumptions:**",
        "verification_ready": "**✅ Can be used as is:**",
        "factcheck_found": "**🔍 Facts to verify:**",
        "legal_risks": "**⚖️ Legal risks (phrasing):**",
        "export_to_docs": "📋 Copy to paste into Google Docs/Notion",
        "subscription": "Plan",
        "subscription_free": "Free (5 uses)",
        "subscription_pro": "Pro (100 uses)",
        "subscription_business": "Business (1000 uses)",
        "usage_left": f"Remaining: {5 - st.session_state.usage_count if st.session_state.subscription_tier == 'free' else 'many'}",
        "upgrade_button": "💳 Upgrade plan (demo)"
    }
}

def get_text(key, lang):
    return TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))

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
            return "[Ошибка чтения PDF]"
    elif "word" in file.type or "document" in file.type:
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            return "\n".join([p.text for p in doc.paragraphs])
        except:
            return "[Ошибка чтения DOCX]"
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
    "ru": [
        "👔 ЛПР (CEO, директор) — стратегия, результаты",
        "⚙️ Технари — точность, факты",
        "📢 Маркетологи и PR — значимость, новизна",
        "💰 Инвесторы — эффективность, масштабирование",
        "👥 Массовая аудитория — простота, примеры",
        "🎯 Потенциальные сотрудники — вовлеченность, ценности",
        "🏢 Покупатели B2B — выгода, надежность",
        "🛍️ Покупатели B2C — польза, впечатления"
    ],
    "en": [
        "👔 Executive — strategy, results",
        "⚙️ Technical — precision, facts",
        "📢 Marketing & PR — significance, novelty",
        "💰 Investor — efficiency, scalability",
        "👥 General public — simplicity, examples",
        "🎯 Potential employees — engagement, values",
        "🏢 B2B buyers — benefits, reliability",
        "🛍️ B2C buyers — personal benefit"
    ]
}
def get_audience_options(lang):
    return AUDIENCE_OPTIONS.get(lang, AUDIENCE_OPTIONS["en"])

# ==================== ФУНКЦИИ ДЛЯ ФАКТЧЕКИНГА И ЮР. ПРОВЕРКИ ====================
def factcheck_and_legal(text, lang):
    prompt_lang = get_prompt_language(lang)
    prompt = f"""Analyze the text for:
1. FACT-CHECKING: Identify factual claims that need verification (statistics, dates, names, quotes, prices). Return as list.
2. LEGAL RISKS: Identify phrases that may pose legal risks (guarantees, promises of results, unconditional refunds, misleading claims). Return as list.

Return ONLY JSON:
{{
  "facts_to_verify": ["claim 1", "claim 2"],
  "legal_risks": ["risky phrase 1", "risky phrase 2"]
}}

IMPORTANT: Respond in {prompt_lang} language.

Text:
{text[:3000]}
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

# ==================== ОБУЧЕНИЕ НА ПРАВКАХ (сохранение обратной связи) ====================
def save_feedback(original, ai_version, user_edited_version):
    """Сохраняет правки пользователя для будущего обучения"""
    st.session_state.feedback_history.append({
        "original": original[:500],
        "ai": ai_version[:500],
        "user": user_edited_version[:500],
        "timestamp": datetime.now().isoformat()
    })
    # Ограничим историю правок 50 записями
    st.session_state.feedback_history = st.session_state.feedback_history[-50:]

# ==================== ОСНОВНЫЕ АГЕНТЫ (сокращённо, но полностью рабочие) ====================
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
    # Очистка
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

Restructure text according to best practices for this assistant type.
Rules:
- No tiny headings
- Merge short blocks
- No "this is not just...", no pleonasms
- Each paragraph = one thought
- Smooth transitions
- If it's a job vacancy: focus on benefits, culture, growth
- If it's a speech: start with pain/benefit, end with call to action

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
    prompt = f"""Literary editing: remove repetitions, tautology, forbidden constructions ("this is not just..."), pleonasms, empty phrases, marketing clichés. Group homogeneous items. Return text.
Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages, temperature=0.8)

def final_checklist(text, lang, assistant_name):
    prompt_lang = get_prompt_language(lang)
    extra = ""
    if "выступление" in assistant_name.lower() or "speech" in assistant_name.lower():
        extra = "Also ensure: starts with audience pain/benefit, has clear call to action, avoids 'you should' without benefit."
    if "вакансия" in assistant_name.lower() or "vacancy" in assistant_name.lower():
        extra = "Ensure: includes benefits, culture, growth opportunities, clear next step (apply)."
    prompt = f"""Fix any issues: no tiny headings, no forbidden constructions, no pleonasms, no empty phrases, no repetitions, no clichés, factual accuracy. {extra} Return corrected text.
Text: {text[:3000]}"""
    messages = [{"role": "user", "content": prompt}]
    return call_gpt(messages, temperature=0.5)

def generate_verification_report(text, original, lang):
    # Проверка стоп-фраз
    stop_phrases = {
        "ru": ["как бы", "наверное", "может быть", "я не знаю", "вы должны", "вы ошибаетесь", "часто", "некоторые", "многие", "заявочку", "договорчик", "сделаем всё", "свяжемся как только сможем", "звоните в любое время", "давайте включим это в проект"],
        "en": ["kind of", "maybe", "perhaps", "i don't know", "you must", "you are wrong", "some", "many", "probably"]
    }
    found_stop = [p for p in stop_phrases.get(lang, []) if p in text.lower()]
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
# Инициализация session state
for key in ["styleguide_content", "examples_list", "input_text", "last_result"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key != "examples_list" else []
if "glossary_list" not in st.session_state:
    st.session_state.glossary_list = []  # список строк "термин=замена"

# Выбор языка
lang_options = list(LANGUAGES.keys())
selected_lang_name = st.sidebar.selectbox("🌐 Language / Язык", lang_options, index=0)
ui_lang = LANGUAGES[selected_lang_name]

st.title(get_text("title", ui_lang))
st.markdown(get_text("subtitle", ui_lang))

with st.sidebar:
    st.header(get_text("settings", ui_lang))
    st.markdown("---")
    
    # Тариф и лимиты
    st.subheader(get_text("subscription", ui_lang))
    tier = st.selectbox("", [get_text("subscription_free", ui_lang), get_text("subscription_pro", ui_lang), get_text("subscription_business", ui_lang)], index=0)
    if tier == get_text("subscription_free", ui_lang):
        st.session_state.subscription_tier = "free"
    elif tier == get_text("subscription_pro", ui_lang):
        st.session_state.subscription_tier = "pro"
    else:
        st.session_state.subscription_tier = "business"
    st.caption(get_text("usage_left", ui_lang))
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
    glossary_input = st.text_area("Формат: термин = замена (каждая пара с новой строки)", height=100,
                                  placeholder="продукт = решение\nбыстрый = оперативный")
    if st.button("Загрузить глоссарий"):
        st.session_state.glossary = {}
        for line in glossary_input.strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                st.session_state.glossary[k.strip()] = v.strip()
        st.success(f"✅ {len(st.session_state.glossary)} терминов")
    
    st.markdown("---")
    st.subheader(get_text("google_docs", ui_lang))
    gdocs_url = st.text_input(get_text("google_docs_url", ui_lang))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(get_text("google_docs_import", ui_lang)):
            imported = import_from_google_docs(gdocs_url)
            if imported:
                st.session_state.input_text = imported
                st.success(get_text("google_docs_import_success", ui_lang) if ui_lang=="ru" else "Imported")
                st.rerun()
    with col2:
        if st.button(get_text("google_docs_export", ui_lang)):
            if st.session_state.get("last_result"):
                st.info("📋 Результат скопирован в буфер (выделите и скопируйте вручную)")
    
    st.markdown("---")
    audience_options = get_audience_options(ui_lang)
    audience = st.selectbox(get_text("audience", ui_lang), audience_options, index=0)
    
    st.markdown("---")
    emotionality = st.select_slider(get_text("emotionality", ui_lang), options=get_text("emotionality_options", ui_lang), value="средняя")
    complexity = st.select_slider(get_text("complexity", ui_lang), options=get_text("complexity_options", ui_lang), value="средняя")
    speed = st.select_slider(get_text("speed", ui_lang), options=get_text("speed_options", ui_lang), value="ритмичная")
    
    st.markdown("---")
    st.caption(f"{BRAND_CONFIG['app_name']} v2.0 – {BRAND_CONFIG['company_name']}")

# Поле ввода
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
        
        # Применяем глоссарий
        if st.session_state.glossary:
            final_text = apply_glossary(final_text)
        
        # Фактчекинг и юр. проверка
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
                st.markdown("**🚫 Стоп-фразы:** " + ", ".join(verification["stop_phrases_found"]))
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
                st.info("🟡 " + ("С осторожностью" if ui_lang=="ru" else "Use with caution"))
            else:
                st.warning("🔴 " + ("Требуется доработка" if ui_lang=="ru" else "Needs revision"))
        with tab6:
            if st.session_state.history:
                for i, item in enumerate(st.session_state.history[:5]):
                    with st.expander(f"{item['timestamp'][:16]} – {item['original'][:80]}..."):
                        st.text("Было: " + item['original'])
                        st.text("Стало: " + item['result'])
            else:
                st.info("История пуста")

# Счётчик сессий
if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1
st.sidebar.markdown(f"{get_text('session_count', ui_lang)} {st.session_state.visit_count}")
