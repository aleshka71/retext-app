import streamlit as st
import openai
import json
import difflib
from datetime import datetime
import os

st.set_page_config(page_title="ReText – Контент-хирург для КП", page_icon="✂️")

PASSWORD = "retext2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        pwd = st.text_input("Введите пароль для доступа к ReText:", type="password")
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("Неверный пароль")
        st.stop()

check_password()

# Инициализация клиента OpenAI (новый синтаксис)
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def call_gpt(messages, model="gpt-4o-mini", temperature=0.7):
    """Универсальный вызов GPT с обработкой ошибок (новый синтаксис)"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Ошибка при вызове GPT: {e}")
        return None

def detect_language(text):
    import re
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    if cyrillic > len(text) * 0.3:
        return "ru"
    else:
        return "en"

def sense_diagnosis(text, lang):
    prompt_ru = """
Ты — эксперт по коммерческим предложениям (КП). Проанализируй КП и верни JSON:

{
  "main_thesis": "Главная мысль КП (одно предложение). Если её нет — сформулируй на основе текста.",
  "secondary_theses": ["второстепенный тезис 1", "тезис 2"],
  "missing_thesis": "Если главной мысли нет — что должно быть главной мыслью?",
  "unproven_claims": ["утверждение без доказательства", ...],
  "hidden_meanings": ["скрытый подтекст", ...],
  "redundant_parts": ["части, которые не работают на продажу", ...],
  "diagnosis": "Краткий вывод (1-2 предложения)"
}

Текст КП:
"""
    prompt_en = """
You are a B2B proposal expert. Analyze the proposal and return JSON:

{
  "main_thesis": "The main selling idea (one sentence). If missing, formulate it.",
  "secondary_theses": ["secondary thesis 1", "thesis 2"],
  "missing_thesis": "If no main thesis, what should it be?",
  "unproven_claims": ["claim without proof", ...],
  "hidden_meanings": ["hidden subtext", ...],
  "redundant_parts": ["parts that don't help sell", ...],
  "diagnosis": "Brief conclusion (1-2 sentences)"
}

Proposal text:
"""
    messages = [{"role": "user", "content": (prompt_ru if lang == "ru" else prompt_en) + text}]
    result = call_gpt(messages)
    try:
        return json.loads(result)
    except:
        return {"error": "Не удалось распарсить JSON", "raw": result}

def restructure(text, text_type, lang):
    structure_ru = """
Структура идеального КП:
1. Боль (понятная клиенту проблема)
2. Решение (одним предложением, УТП)
3. Как это работает (механизм)
4. Доказательства (кейс, цифры)
5. Цена и условия
6. Призыв к действию (однозначный)

Перестрой текст по этой структуре. Добавь короткие переходы. Удали лишнее.
Верни только переработанный текст.
"""
    structure_en = """
Ideal proposal structure:
1. Pain (clear client problem)
2. Solution (one sentence, USP)
3. How it works (mechanism)
4. Proof (case, numbers)
5. Price and terms
6. Call to action (unambiguous)

Restructure the text accordingly. Add short transitions. Remove fluff.
Return only the rewritten text.
"""
    messages = [{"role": "user", "content": (structure_ru if lang == "ru" else structure_en) + "\n\nТекст:\n" + text}]
    return call_gpt(messages)

def adjust_tone(text, audience, emotionality, complexity, speed, lang):
    tone_ru = f"""
Измени тональность текста согласно параметрам:
- Аудитория: {audience}
- Эмоциональность: {emotionality} (низкая/средняя/высокая)
- Сложность: {complexity} (простая/средняя/высокая)
- Скорость: {speed} (ритмичная/размеренная/прерывистая)

Сохрани смысл, но измени стиль. Верни только текст.
"""
    tone_en = f"""
Adjust the tone according to:
- Audience: {audience}
- Emotionality: {emotionality} (low/medium/high)
- Complexity: {complexity} (simple/medium/high)
- Speed: {speed} (rhythmic/measured/jerky)

Keep the meaning, change the style. Return only text.
"""
    messages = [{"role": "user", "content": (tone_ru if lang == "ru" else tone_en) + "\n\nТекст:\n" + text}]
    return call_gpt(messages)

def add_engagement(text, lang):
    engage_ru = """
Добавь в текст вовлекающие элементы:
- Заголовок-крючок (если нет)
- Вопрос в первом абзаце
- Разбей на абзацы по 1-3 предложения
- Добавь 3-4 подзаголовка
- Один контраст («раньше / теперь» или «было / стало»)
- Один конкретный пример
- Выдели **жирным** ключевые фразы (10-15% текста)

Верни итоговый текст.
"""
    engage_en = """
Add engagement elements:
- Hook title (if missing)
- Question in first paragraph
- Break into paragraphs of 1-3 sentences
- Add 3-4 subheadings
- One contrast ("before / now")
- One concrete example
- **Bold** key phrases (10-15% of text)

Return final text.
"""
    messages = [{"role": "user", "content": (engage_ru if lang == "ru" else engage_en) + "\n\nТекст:\n" + text}]
    return call_gpt(messages)

def final_check(original, rewritten, lang):
    check_ru = f"""
Сравни исходный и переработанный текст. Верни JSON:
{{
  "is_better": true/false,
  "changes_summary": "что изменилось и почему (1-2 абзаца)",
  "improvements": ["улучшение 1", "улучшение 2"],
  "score_out_of_10": 8
}}

Исходный:
{original}

Переработанный:
{rewritten}
"""
    messages = [{"role": "user", "content": check_ru if lang == "ru" else check_ru.replace("Исходный", "Original").replace("Переработанный", "Rewritten")}]
    return call_gpt(messages)

def visual_diff(original, rewritten):
    diff = difflib.HtmlDiff(wrapcolumn=80).make_file(
        original.splitlines(), rewritten.splitlines(),
        fromdesc="Было", todesc="Стало", context=True, numlines=2
    )
    return diff

st.title("✂️ ReText – Контент-хирург для коммерческих предложений")
st.markdown("Переделываем унылые КП в продающие, вовлекающие, понятные.")

with st.sidebar:
    st.header("Настройки")
    language_option = st.selectbox("Язык", ["Авто (определить)", "Русский", "English"])
    st.markdown("---")
    st.subheader("Параметры тональности (можно скорректировать)")
    audience = st.selectbox("Аудитория", ["ЛПР", "Технари", "Маркетологи", "Инвесторы", "Массовая"])
    emotionality = st.select_slider("Эмоциональность", options=["низкая", "средняя", "высокая"], value="средняя")
    complexity = st.select_slider("Сложность", options=["простая", "средняя", "высокая"], value="средняя")
    speed = st.select_slider("Скорость/ритм", options=["ритмичная", "размеренная", "прерывистая"], value="ритмичная")
    
    st.markdown("---")
    st.caption("ReText v0.1 для TEXTUM")

input_text = st.text_area("Вставьте текст коммерческого предложения (до 8000 символов):", height=300, max_chars=8000)

if st.button("🚀 Запустить ReText"):
    if not input_text.strip():
        st.warning("Пожалуйста, введите текст.")
    else:
        if language_option == "Авто (определить)":
            lang = detect_language(input_text)
            st.info(f"Определён язык: {'Русский' if lang == 'ru' else 'English'}")
        else:
            lang = "ru" if language_option == "Русский" else "en"
        
        with st.spinner("1/5 Смысловая диагностика..."):
            diagnosis = sense_diagnosis(input_text, lang)
        st.subheader("🔍 Смысловая диагностика (предварительная)")
        if "error" in diagnosis:
            st.json(diagnosis)
        else:
            st.write(f"**Главная мысль:** {diagnosis.get('main_thesis', '—')}")
            st.write(f"**Диагноз:** {diagnosis.get('diagnosis', '—')}")
            if diagnosis.get("redundant_parts"):
                st.write("**Лишние части:** " + ", ".join(diagnosis["redundant_parts"]))
        
        corrected_main_thesis = st.text_input("Если главная мысль неверна, исправьте:", value=diagnosis.get("main_thesis", ""))
        if corrected_main_thesis and corrected_main_thesis != diagnosis.get("main_thesis"):
            st.info(f"Будем использовать: {corrected_main_thesis}")
        
        with st.spinner("2/5 Реструктуризация..."):
            restructured = restructure(input_text, "КП", lang)
        with st.spinner("3/5 Настройка тональности..."):
            toned = adjust_tone(restructured, audience, emotionality, complexity, speed, lang)
        with st.spinner("4/5 Добавление вовлекающих элементов..."):
            final_text = add_engagement(toned, lang)
        with st.spinner("5/5 Формирование отчёта..."):
            report = final_check(input_text, final_text, lang)
        
        st.success("Готово!")
        tab1, tab2, tab3, tab4 = st.tabs(["📄 Стало", "📊 Отчёт", "🔍 Визуальное сравнение", "📜 Было"])
        
        with tab1:
            st.markdown(final_text)
        with tab2:
            try:
                report_json = json.loads(report)
                st.json(report_json)
            except:
                st.write(report)
        with tab3:
            diff_html = visual_diff(input_text, final_text)
            st.components.v1.html(diff_html, height=500)
        with tab4:
            st.text(input_text)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "lang": lang,
            "audience": audience,
            "text_length": len(input_text)
        }
        try:
            with open("usage_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except:
            pass

if "visit_count" not in st.session_state:
    st.session_state.visit_count = 0
st.session_state.visit_count += 1
st.sidebar.markdown(f"**Сессий за время работы:** {st.session_state.visit_count}")
