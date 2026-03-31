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
    "🇨🇳 中文": "zh"
}

# Тексты интерфейса на всех языках
TEXTS = {
    "ru": {
        "title": "✂️ ReText – Контент-хирург для коммерческих предложений",
        "subtitle": "Переделываем унылые КП в продающие, вовлекающие, понятные.",
        "settings": "Настройки",
        "language": "Язык интерфейса",
        "tone_params": "Параметры тональности (можно скорректировать)",
        "audience": "Аудитория",
        "audience_options": ["ЛПР", "Технари", "Маркетологи", "Инвесторы", "Массовая"],
        "emotionality": "Эмоциональность",
        "emotionality_options": ["низкая", "средняя", "высокая"],
        "complexity": "Сложность",
        "complexity_options": ["простая", "средняя", "высокая"],
        "speed": "Скорость/ритм",
        "speed_options": ["ритмичная", "размеренная", "прерывистая"],
        "text_input_label": "Вставьте текст коммерческого предложения (до 8000 символов):",
        "run_button": "🚀 Запустить ReText",
        "spinner1": "1/5 Смысловая диагностика...",
        "spinner2": "2/5 Реструктуризация...",
        "spinner3": "3/5 Настройка тональности...",
        "spinner4": "4/5 Добавление вовлекающих элементов...",
        "spinner5": "5/5 Формирование отчёта...",
        "diagnosis_title": "🔍 Смысловая диагностика (предварительная)",
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
        "session_count": "Сессий за время работы:",
        "warning_empty": "Пожалуйста, введите текст.",
        "lang_detected": "Определён язык:",
        "lang_russian": "Русский"
    },
    "en": {
        "title": "✂️ ReText – Content Surgeon for Business Proposals",
        "subtitle": "Turn boring proposals into selling, engaging, clear documents.",
        "settings": "Settings",
        "language": "Interface language",
        "tone_params": "Tone parameters (adjustable)",
        "audience": "Audience",
        "audience_options": ["Executive", "Technical", "Marketing", "Investor", "General"],
        "emotionality": "Emotionality",
        "emotionality_options": ["low", "medium", "high"],
        "complexity": "Complexity",
        "complexity_options": ["simple", "medium", "complex"],
        "speed": "Pacing",
        "speed_options": ["rhythmic", "measured", "jerky"],
        "text_input_label": "Paste your business proposal text (up to 8000 chars):",
        "run_button": "🚀 Run ReText",
        "spinner1": "1/5 Sense diagnosis...",
        "spinner2": "2/5 Restructuring...",
        "spinner3": "3/5 Tone adjustment...",
        "spinner4": "4/5 Adding engagement elements...",
        "spinner5": "5/5 Generating report...",
        "diagnosis_title": "🔍 Sense diagnosis (preliminary)",
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
        "session_count": "Sessions during runtime:",
        "warning_empty": "Please enter text.",
        "lang_detected": "Language detected:",
        "lang_russian": "Russian"
    },
    "de": {
        "title": "✂️ ReText – Content-Chirurg für Geschäftsangebote",
        "subtitle": "Verwandeln Sie langweilige Angebote in verkaufsstarke, ansprechende Texte.",
        "settings": "Einstellungen",
        "language": "Oberflächensprache",
        "tone_params": "Tonfall-Parameter (anpassbar)",
        "audience": "Zielgruppe",
        "audience_options": ["Führungskraft", "Techniker", "Marketing", "Investor", "Allgemein"],
        "emotionality": "Emotionalität",
        "emotionality_options": ["niedrig", "mittel", "hoch"],
        "complexity": "Komplexität",
        "complexity_options": ["einfach", "mittel", "komplex"],
        "speed": "Rhythmus",
        "speed_options": ["rhythmisch", "gemäßigt", "ruckartig"],
        "text_input_label": "Fügen Sie Ihren Angebotstext ein (bis zu 8000 Zeichen):",
        "run_button": "🚀 ReText starten",
        "spinner1": "1/5 Sinn-Diagnose...",
        "spinner2": "2/5 Umstrukturierung...",
        "spinner3": "3/5 Tonfall-Anpassung...",
        "spinner4": "4/5 Engagement-Elemente hinzufügen...",
        "spinner5": "5/5 Bericht erstellen...",
        "diagnosis_title": "🔍 Sinn-Diagnose (vorläufig)",
        "main_thesis": "**Hauptthese:**",
        "diagnosis": "**Diagnose:**",
        "redundant_parts": "**Redundante Teile:**",
        "correct_thesis": "Wenn die Hauptthese falsch ist, korrigieren Sie:",
        "using_thesis": "Verwendet wird:",
        "success": "Fertig!",
        "tab_result": "📄 Ergebnis",
        "tab_report": "📊 Bericht",
        "tab_diff": "🔍 Visueller Vergleich",
        "tab_original": "📜 Original",
        "session_count": "Sitzungen während der Laufzeit:",
        "warning_empty": "Bitte geben Sie Text ein.",
        "lang_detected": "Erkannte Sprache:",
        "lang_russian": "Russisch"
    },
    "fr": {
        "title": "✂️ ReText – Chirurgien de contenu pour propositions commerciales",
        "subtitle": "Transformez les propositions ennuyeuses en textes convaincants et engageants.",
        "settings": "Paramètres",
        "language": "Langue de l'interface",
        "tone_params": "Paramètres de ton (ajustables)",
        "audience": "Public",
        "audience_options": ["Dirigeant", "Technique", "Marketing", "Investisseur", "Grand public"],
        "emotionality": "Émotionnalité",
        "emotionality_options": ["faible", "moyenne", "élevée"],
        "complexity": "Complexité",
        "complexity_options": ["simple", "moyenne", "complexe"],
        "speed": "Rythme",
        "speed_options": ["rythmé", "mesuré", "saccadé"],
        "text_input_label": "Collez votre proposition commerciale (jusqu'à 8000 caractères) :",
        "run_button": "🚀 Lancer ReText",
        "spinner1": "1/5 Diagnostic de sens...",
        "spinner2": "2/5 Restructuration...",
        "spinner3": "3/5 Ajustement du ton...",
        "spinner4": "4/5 Ajout d'éléments engageants...",
        "spinner5": "5/5 Génération du rapport...",
        "diagnosis_title": "🔍 Diagnostic de sens (préliminaire)",
        "main_thesis": "**Thèse principale :**",
        "diagnosis": "**Diagnostic :**",
        "redundant_parts": "**Parties redondantes :**",
        "correct_thesis": "Si la thèse principale est incorrecte, corrigez :",
        "using_thesis": "Nous utiliserons :",
        "success": "Terminé !",
        "tab_result": "📄 Résultat",
        "tab_report": "📊 Rapport",
        "tab_diff": "🔍 Comparaison visuelle",
        "tab_original": "📜 Original",
        "session_count": "Sessions depuis le lancement :",
        "warning_empty": "Veuillez saisir du texte.",
        "lang_detected": "Langue détectée :",
        "lang_russian": "Russe"
    },
    "es": {
        "title": "✂️ ReText – Cirujano de contenido para propuestas comerciales",
        "subtitle": "Convierte propuestas aburridas en textos persuasivos, atractivos y claros.",
        "settings": "Configuración",
        "language": "Idioma de la interfaz",
        "tone_params": "Parámetros de tono (ajustables)",
        "audience": "Audiencia",
        "audience_options": ["Directivo", "Técnico", "Marketing", "Inversor", "Público general"],
        "emotionality": "Emocionalidad",
        "emotionality_options": ["baja", "media", "alta"],
        "complexity": "Complejidad",
        "complexity_options": ["simple", "media", "compleja"],
        "speed": "Ritmo",
        "speed_options": ["rítmico", "pausado", "entre cortado"],
        "text_input_label": "Pegue su propuesta comercial (hasta 8000 caracteres):",
        "run_button": "🚀 Ejecutar ReText",
        "spinner1": "1/5 Diagnóstico de sentido...",
        "spinner2": "2/5 Reestructuración...",
        "spinner3": "3/5 Ajuste de tono...",
        "spinner4": "4/5 Agregando elementos atractivos...",
        "spinner5": "5/5 Generando informe...",
        "diagnosis_title": "🔍 Diagnóstico de sentido (preliminar)",
        "main_thesis": "**Tesis principal:**",
        "diagnosis": "**Diagnóstico:**",
        "redundant_parts": "**Partes redundantes:**",
        "correct_thesis": "Si la tesis principal es incorrecta, corríjala:",
        "using_thesis": "Usaremos:",
        "success": "¡Listo!",
        "tab_result": "📄 Resultado",
        "tab_report": "📊 Informe",
        "tab_diff": "🔍 Comparación visual",
        "tab_original": "📜 Original",
        "session_count": "Sesiones durante la ejecución:",
        "warning_empty": "Por favor, ingrese texto.",
        "lang_detected": "Idioma detectado:",
        "lang_russian": "Ruso"
    },
    "zh": {
        "title": "✂️ ReText – 商业提案内容外科医生",
        "subtitle": "将枯燥的提案转化为有说服力、引人入胜、清晰明了的文本。",
        "settings": "设置",
        "language": "界面语言",
        "tone_params": "语气参数（可调整）",
        "audience": "受众",
        "audience_options": ["高管", "技术人员", "市场营销", "投资者", "大众"],
        "emotionality": "情感度",
        "emotionality_options": ["低", "中", "高"],
        "complexity": "复杂度",
        "complexity_options": ["简单", "中等", "复杂"],
        "speed": "节奏",
        "speed_options": ["节奏感强", "平缓", "断续"],
        "text_input_label": "粘贴您的商业提案文本（最多8000字符）：",
        "run_button": "🚀 运行 ReText",
        "spinner1": "1/5 语义诊断...",
        "spinner2": "2/5 结构重组...",
        "spinner3": "3/5 语气调整...",
        "spinner4": "4/5 添加吸引元素...",
        "spinner5": "5/5 生成报告...",
        "diagnosis_title": "🔍 语义诊断（初步）",
        "main_thesis": "**核心论点：**",
        "diagnosis": "**诊断：**",
        "redundant_parts": "**冗余部分：**",
        "correct_thesis": "如果核心论点不正确，请修正：",
        "using_thesis": "将使用：",
        "success": "完成！",
        "tab_result": "📄 结果",
        "tab_report": "📊 报告",
        "tab_diff": "🔍 视觉对比",
        "tab_original": "📜 原文",
        "session_count": "运行期间会话数：",
        "warning_empty": "请输入文本。",
        "lang_detected": "检测到的语言：",
        "lang_russian": "俄语"
    }
}

# Функция получения текста на выбранном языке
def t(key, lang):
    return TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))

# Инициализация клиента OpenAI
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

def detect_language(text):
    import re
    cyrillic = len(re.findall(r'[а-яА-ЯёЁ]', text))
    if cyrillic > len(text) * 0.3:
        return "ru"
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    if chinese > len(text) * 0.3:
        return "zh"
    return "en"

def sense_diagnosis(text, lang):
    prompts = {
        "ru": f"""Ты — эксперт по коммерческим предложениям (КП). Проанализируй КП и верни ТОЛЬКО JSON, без пояснений и без маркеров разметки.

Формат ответа:
{{
  "main_thesis": "Главная мысль КП (одно предложение). Если её нет — сформулируй на основе текста.",
  "secondary_theses": ["второстепенный тезис 1", "тезис 2"],
  "missing_thesis": "Если главной мысли нет — что должно быть главной мыслью?",
  "unproven_claims": ["утверждение без доказательства"],
  "hidden_meanings": ["скрытый подтекст"],
  "redundant_parts": ["части, которые не работают на продажу"],
  "diagnosis": "Краткий вывод (1-2 предложения)"
}}

Текст КП:
""",
        "en": f"""You are a B2B proposal expert. Analyze the proposal and return ONLY JSON, without explanations and without markdown markers.

Format:
{{
  "main_thesis": "The main selling idea (one sentence). If missing, formulate it.",
  "secondary_theses": ["secondary thesis 1", "thesis 2"],
  "missing_thesis": "If no main thesis, what should it be?",
  "unproven_claims": ["claim without proof"],
  "hidden_meanings": ["hidden subtext"],
  "redundant_parts": ["parts that don't help sell"],
  "diagnosis": "Brief conclusion (1-2 sentences)"
}}

Proposal text:
""",
        "de": f"""Du bist ein Experte für Geschäftsangebote. Analysiere das Angebot und gib NUR JSON zurück, ohne Erklärungen und ohne Markdown-Markierungen.

Format:
{{
  "main_thesis": "Die Hauptaussage des Angebots (ein Satz). Falls fehlend, formuliere sie.",
  "secondary_theses": ["Nebenthese 1", "These 2"],
  "missing_thesis": "Wenn keine Hauptaussage vorhanden ist, was sollte sie sein?",
  "unproven_claims": ["Behauptung ohne Beweis"],
  "hidden_meanings": ["verborgene Untertöne"],
  "redundant_parts": ["Teile, die nicht zum Verkauf beitragen"],
  "diagnosis": "Kurze Zusammenfassung (1-2 Sätze)"
}}

Angebotstext:
""",
        "fr": f"""Vous êtes un expert en propositions commerciales. Analysez la proposition et renvoyez UNIQUEMENT du JSON, sans explications ni marqueurs Markdown.

Format:
{{
  "main_thesis": "L'idée principale de vente (une phrase). Si manquante, formulez-la.",
  "secondary_theses": ["thèse secondaire 1", "thèse 2"],
  "missing_thesis": "S'il n'y a pas d'idée principale, quelle devrait-elle être ?",
  "unproven_claims": ["affirmation sans preuve"],
  "hidden_meanings": ["sous-entendus cachés"],
  "redundant_parts": ["parties qui ne contribuent pas à la vente"],
  "diagnosis": "Conclusion brève (1-2 phrases)"
}}

Texte de la proposition:
""",
        "es": f"""Eres un experto en propuestas comerciales. Analiza la propuesta y devuelve SOLO JSON, sin explicaciones ni marcadores Markdown.

Formato:
{{
  "main_thesis": "La idea principal de venta (una frase). Si falta, formúlela.",
  "secondary_theses": ["tesis secundaria 1", "tesis 2"],
  "missing_thesis": "Si no hay idea principal, ¿cuál debería ser?",
  "unproven_claims": ["afirmación sin prueba"],
  "hidden_meanings": ["significados ocultos"],
  "redundant_parts": ["partes que no ayudan a vender"],
  "diagnosis": "Conclusión breve (1-2 frases)"
}}

Texto de la propuesta:
""",
        "zh": f"""您是商业提案专家。分析提案并仅返回 JSON，不要解释和 Markdown 标记。

格式：
{{
  "main_thesis": "核心销售主张（一句话）。如果没有，请根据文本制定。",
  "secondary_theses": ["次要论点 1", "论点 2"],
  "missing_thesis": "如果没有核心思想，应该是什么？",
  "unproven_claims": ["未经证实的说法"],
  "hidden_meanings": ["隐藏含义"],
  "redundant_parts": ["无助于销售的部分"],
  "diagnosis": "简要结论（1-2 句话）"
}}

提案文本：
"""
    }
    prompt = prompts.get(lang, prompts["en"])
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

def restructure(text, text_type, lang):
    prompts = {
        "ru": f"""Структура идеального КП:
1. Боль (понятная клиенту проблема)
2. Решение (одним предложением, УТП)
3. Как это работает (механизм)
4. Доказательства (кейс, цифры)
5. Цена и условия
6. Призыв к действию (однозначный)

Перестрой текст по этой структуре. Добавь короткие переходы. Удали лишнее.
Верни только переработанный текст.

Текст:
""",
        "en": f"""Ideal proposal structure:
1. Pain (clear client problem)
2. Solution (one sentence, USP)
3. How it works (mechanism)
4. Proof (case, numbers)
5. Price and terms
6. Call to action (unambiguous)

Restructure the text accordingly. Add short transitions. Remove fluff.
Return only the rewritten text.

Text:
""",
        "de": f"""Ideale Angebotsstruktur:
1. Schmerz (klares Kundenproblem)
2. Lösung (ein Satz, Alleinstellungsmerkmal)
3. Wie es funktioniert (Mechanismus)
4. Beweise (Fallbeispiel, Zahlen)
5. Preis und Konditionen
6. Handlungsaufforderung (eindeutig)

Baue den Text nach dieser Struktur um. Füge kurze Übergänge hinzu. Entferne überflüssiges.
Gib nur den überarbeiteten Text zurück.

Text:
""",
        "fr": f"""Structure idéale d'une proposition :
1. Problème (problème clair du client)
2. Solution (une phrase, USP)
3. Comment ça fonctionne (mécanisme)
4. Preuves (cas, chiffres)
5. Prix et conditions
6. Appel à l'action (sans ambiguïté)

Restructurez le texte selon cette structure. Ajoutez de courtes transitions. Supprimez le superflu.
Retournez uniquement le texte réécrit.

Texte :
""",
        "es": f"""Estructura ideal de propuesta:
1. Dolor (problema claro del cliente)
2. Solución (una frase, USP)
3. Cómo funciona (mecanismo)
4. Pruebas (caso, números)
5. Precio y condiciones
6. Llamada a la acción (inequívoca)

Reestructura el texto según esta estructura. Agrega transiciones cortas. Elimina lo superfluo.
Devuelve solo el texto reescrito.

Texto:
""",
        "zh": f"""理想提案结构：
1. 痛点（明确的客户问题）
2. 解决方案（一句话，独特卖点）
3. 工作原理（机制）
4. 证据（案例、数据）
5. 价格与条款
6. 行动号召（明确）

按照此结构重组文本。添加简短过渡。删除冗余内容。
仅返回重写后的文本。

文本：
"""
    }
    messages = [{"role": "user", "content": prompts.get(lang, prompts["en"]) + text}]
    return call_gpt(messages)

def adjust_tone(text, audience, emotionality, complexity, speed, lang):
    prompts = {
        "ru": f"""Измени тональность текста согласно параметрам:
- Аудитория: {audience}
- Эмоциональность: {emotionality}
- Сложность: {complexity}
- Скорость/ритм: {speed}

Сохрани смысл, но измени стиль. Верни только текст.

Текст:
""",
        "en": f"""Adjust the tone according to:
- Audience: {audience}
- Emotionality: {emotionality}
- Complexity: {complexity}
- Pacing: {speed}

Keep the meaning, change the style. Return only text.

Text:
""",
        "de": f"""Passe den Tonfall gemäß den Parametern an:
- Zielgruppe: {audience}
- Emotionalität: {emotionality}
- Komplexität: {complexity}
- Rhythmus: {speed}

Behalte den Sinn bei, ändere den Stil. Gib nur den Text zurück.

Text:
""",
        "fr": f"""Ajustez le ton selon les paramètres :
- Public : {audience}
- Émotionnalité : {emotionality}
- Complexité : {complexity}
- Rythme : {speed}

Gardez le sens, changez le style. Retournez uniquement le texte.

Texte :
""",
        "es": f"""Ajusta el tono según los parámetros:
- Audiencia: {audience}
- Emocionalidad: {emotionality}
- Complejidad: {complexity}
- Ritmo: {speed}

Mantén el significado, cambia el estilo. Devuelve solo el texto.

Texto:
""",
        "zh": f"""根据以下参数调整语气：
- 受众：{audience}
- 情感度：{emotionality}
- 复杂度：{complexity}
- 节奏：{speed}

保持含义，改变风格。仅返回文本。

文本：
"""
    }
    messages = [{"role": "user", "content": prompts.get(lang, prompts["en"]) + text}]
    return call_gpt(messages)

def add_engagement(text, lang):
    prompts = {
        "ru": """Добавь в текст вовлекающие элементы:
- Заголовок-крючок (если нет)
- Вопрос в первом абзаце
- Разбей на абзацы по 1-3 предложения
- Добавь 3-4 подзаголовка
- Один контраст («раньше / теперь» или «было / стало»)
- Один конкретный пример
- Выдели **жирным** ключевые фразы (10-15% текста)

Верни итоговый текст.

Текст:
""",
        "en": """Add engagement elements:
- Hook title (if missing)
- Question in first paragraph
- Break into paragraphs of 1-3 sentences
- Add 3-4 subheadings
- One contrast ("before / now")
- One concrete example
- **Bold** key phrases (10-15% of text)

Return final text.

Text:
""",
        "de": """Füge Engagement-Elemente hinzu:
- Aufmerksamkeitsstarker Titel (falls fehlend)
- Frage im ersten Absatz
- Unterteile in Absätze mit 1-3 Sätzen
- Füge 3-4 Zwischenüberschriften hinzu
- Einen Kontrast ("früher / jetzt")
- Ein konkretes Beispiel
- **Fett** hervorgehobene Schlüsselphrasen (10-15% des Textes)

Gib den endgültigen Text zurück.

Text:
""",
        "fr": """Ajoutez des éléments engageants :
- Titre accrocheur (si absent)
- Question dans le premier paragraphe
- Divisez en paragraphes de 1 à 3 phrases
- Ajoutez 3-4 sous-titres
- Un contraste (« avant / maintenant »)
- Un exemple concret
- Mettez **en gras** les phrases clés (10-15% du texte)

Retournez le texte final.

Texte :
""",
        "es": """Agrega elementos atractivos:
- Título gancho (si falta)
- Pregunta en el primer párrafo
- Divide en párrafos de 1-3 oraciones
- Agrega 3-4 subtítulos
- Un contraste (« antes / ahora »)
- Un ejemplo concreto
- **Negrita** para frases clave (10-15% del texto)

Devuelve el texto final.

Texto:
""",
        "zh": """添加吸引元素：
- 钩子标题（如果没有）
- 第一段加入问题
- 分成 1-3 句的段落
- 添加 3-4 个小标题
- 一处对比（"以前 / 现在"）
- 一个具体例子
- **加粗**关键短语（占文本 10-15%）

返回最终文本。

文本：
"""
    }
    messages = [{"role": "user", "content": prompts.get(lang, prompts["en"]) + text}]
    return call_gpt(messages)

def final_check(original, rewritten, lang):
    prompts = {
        "ru": f"""Сравни исходный и переработанный текст. Верни ТОЛЬКО JSON, без пояснений и без маркеров разметки.

Формат:
{{
  "is_better": true,
  "changes_summary": "что изменилось и почему (1-2 абзаца)",
  "improvements": ["улучшение 1", "улучшение 2"],
  "score_out_of_10": 8
}}

Исходный:
{original}

Переработанный:
{rewritten}
""",
        "en": f"""Compare original and rewritten text. Return ONLY JSON, without explanations and without markdown markers.

Format:
{{
  "is_better": true,
  "changes_summary": "what changed and why (1-2 paragraphs)",
  "improvements": ["improvement 1", "improvement 2"],
  "score_out_of_10": 8
}}

Original:
{original}

Rewritten:
{rewritten}
""",
        "de": f"""Vergleiche den ursprünglichen und den überarbeiteten Text. Gib NUR JSON zurück, ohne Erklärungen und ohne Markdown-Markierungen.

Format:
{{
  "is_better": true,
  "changes_summary": "was sich geändert hat und warum (1-2 Absätze)",
  "improvements": ["Verbesserung 1", "Verbesserung 2"],
  "score_out_of_10": 8
}}

Original:
{original}

Überarbeitet:
{rewritten}
""",
        "fr": f"""Compare le texte original et le texte réécrit. Renvoie UNIQUEMENT du JSON, sans explications ni marqueurs Markdown.

Format:
{{
  "is_better": true,
  "changes_summary": "ce qui a changé et pourquoi (1-2 paragraphes)",
  "improvements": ["amélioration 1", "amélioration 2"],
  "score_out_of_10": 8
}}

Original :
{original}

Réécrit :
{rewritten}
""",
        "es": f"""Compara el texto original y el texto reescrito. Devuelve SOLO JSON, sin explicaciones ni marcadores Markdown.

Formato:
{{
  "is_better": true,
  "changes_summary": "lo que cambió y por qué (1-2 párrafos)",
  "improvements": ["mejora 1", "mejora 2"],
  "score_out_of_10": 8
}}

Original:
{original}

Reescrito:
{rewritten}
""",
        "zh": f"""比较原文和重写后的文本。仅返回 JSON，不要解释和 Markdown 标记。

格式：
{{
  "is_better": true,
  "changes_summary": "更改了什么以及为什么（1-2 段）",
  "improvements": ["改进 1", "改进 2"],
  "score_out_of_10": 8
}}

原文：
{original}

重写后：
{rewritten}
"""
    }
    messages = [{"role": "user", "content": prompts.get(lang, prompts["en"])}]
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
        fromdesc="Было", todesc="Стало", context=True, numlines=2
    )
    return diff

# ==================== ОСНОВНОЙ ИНТЕРФЕЙС ====================

# Выбор языка
lang_options = list(LANGUAGES.keys())
selected_lang_name = st.sidebar.selectbox("🌐 Language / Язык", lang_options, index=0)
ui_lang = LANGUAGES[selected_lang_name]

st.title(t("title", ui_lang))
st.markdown(t("subtitle", ui_lang))

with st.sidebar:
    st.header(t("settings", ui_lang))
    st.markdown("---")
    st.subheader(t("tone_params", ui_lang))
    audience = st.selectbox(t("audience", ui_lang), TEXTS[ui_lang]["audience_options"])
    emotionality = st.select_slider(t("emotionality", ui_lang), options=TEXTS[ui_lang]["emotionality_options"], value=TEXTS[ui_lang]["emotionality_options"][1])
    complexity = st.select_slider(t("complexity", ui_lang), options=TEXTS[ui_lang]["complexity_options"], value=TEXTS[ui_lang]["complexity_options"][1])
    speed = st.select_slider(t("speed", ui_lang), options=TEXTS[ui_lang]["speed_options"], value=TEXTS[ui_lang]["speed_options"][0])
    
    st.markdown("---")
    st.caption("ReText v0.2 для TEXTUM")

input_text = st.text_area(t("text_input_label", ui_lang), height=300, max_chars=8000)

if st.button(t("
