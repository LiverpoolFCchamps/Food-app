import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import cv2
from pyzbar.pyzbar import decode

# Настройка на страницата с по-голяма ширина
st.set_page_config(page_title="Здравен Скенер", page_icon="🛡️", layout="centered")

# --- СТИЛИЗИРАНЕ ЗА ПО-ГОЛЯМ КOД И ЕЛЕМЕНТИ (CSS) ---
st.markdown("""
    <style>
        html, body, [data-testid="stWidgetLabel"] p {
            font-size: 20px !important;
        }
        .stButton>button {
            font-size: 22px !important;
            padding: 15px 30px !important;
            width: 100%;
            border-radius: 12px;
        }
        .critical-box {
            background-color: #ffebee;
            border-left: 6px solid #d32f2f;
            padding: 15px;
            border-radius: 5px;
            color: #c62828;
            font-weight: bold;
            font-size: 20px;
            margin-bottom: 15px;
        }
        .harmful-box {
            background-color: #fff3e0;
            border-left: 6px solid #f57c00;
            padding: 12px;
            border-radius: 5px;
            color: #e65100;
            font-size: 18px;
            margin-bottom: 10px;
        }
        .safe-box {
            background-color: #e8f5e9;
            border-left: 6px solid #2e7d32;
            padding: 12px;
            border-radius: 5px;
            color: #1b5e20;
            font-size: 18px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --- СИМУЛИРАНА БАЗА ДАННИ ---
PRODUCTS_DB = {
    "4000175123456": {
        "name": "Шоколадов десерт",
        "ingredients": ["захар", "палмово масло", "Е471", "соев лецитин", "глутен"]
    },
    "8410012345678": {
        "name": "Газирана напитка (Кола)",
        "ingredients": ["вода", "аспартам", "Е211", "фосфорна киселина", "захар"]
    }
}

INGREDIENTS_INFO = {
    "захар": {"harmful": True, "desc": "Бърз въглехидрат с висок гликемичен индекс. Предизвиква резки скокове на глюкозата.", "triggers": ["Диабет"]},
    "палмово масло": {"harmful": True, "desc": "Хидрогенирана мазнина. Повишава лошия холестерол (LDL) и уврежда артериите.", "triggers": ["Хипертония (Високо кръвно)"]},
    "аспартам": {"harmful": True, "desc": "Изкуствен подсладител. Може да повлияе негативно на нервната система при честа употреба.", "triggers": ["Диабет"]},
    "глутен": {"harmful": False, "desc": "Протеин в житните култури. Напълно безопасен, освен при изявена нетолерантност.", "triggers": ["Глутенова / Лактозна непоносимост"]},
    "Е211": {"harmful": True, "desc": "Натриев бензоат (консервант). Може да предизвика силни алергични реакции.", "triggers": ["Стомашни проблеми / Язва"]},
    "Е471": {"harmful": False, "desc": "Емулгатор от мастни киселини. Счита се за безопасен за масова консумация.", "triggers": []},
    "соев лецитин": {"harmful": False, "desc": "Емулгатор. Може да съдържа следи от соеви алергени.", "triggers": []},
    "вода": {"harmful": False, "desc": "Чиста филтрирана вода. Напълно безопасна за организма.", "triggers": []},
    "фосфорна киселина": {"harmful": True, "desc": "Дразни лигавицата на стомаха и разрушава зъбния емайл.", "triggers": ["Стомашни проблеми / Язва"]}
}

# --- ИНСТРУМЕНТ ЗА ОБРАБОТКА НА ВИДЕОТО ---
# Проверява всеки кадър от камерата за наличие на баркод
class BarcodeProcessor(VideoProcessorBase):
    def __init__(self):
        self.detected_barcode = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = decode(img)
        
        for barcode in barcodes:
            self.detected_barcode = barcode.data.decode('utf-8')
            # Рисува зелен правоъгълник около намерения баркод
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
        return frame.from_ndarray(img, format="bgr24")

# --- СТАРТ НА СТРАНИЦАТА ---
st.title("🛡️ Здравен Продуктов Скенер")

# СЕКЦИЯ 1: Избор на здравословни проблеми
st.header("1. Изберете вашите здравословни проблеми:")
selected_issues = []
col1, col2 = st.columns(2)

with col1:
    if st.checkbox("🩸 Диабет / Кръвна захар"): selected_issues.append("Диабет")
    if st.checkbox("🫀 Хипертония (Високо кръвно)"): selected_issues.append("Хипертония (Високо кръвно)")
with col2:
    if st.checkbox("🤢 Стомашни проблеми / Язва"): selected_issues.append("Стомашни проблеми / Язва")
    if st.checkbox("🌾 Глутенова / Лактозна непоносимост"): selected_issues.append("Глутенова / Лактозна непоносимост")

st.markdown("---")

# СЕКЦИЯ 2: Сканиране чрез видео
st.header("2. Сканирайте баркода на продукта:")

# Инициализиране на състояние за запазване на баркода
if "barcode" not in st.session_state:
    st.session_state.barcode = None

# Стрийминг от камерата
ctx = webrtc_streamer(
    key="barcode-scanner", 
    video_processor_factory=BarcodeProcessor,
    rtc_configuration={"iceServers": [{"urls": ["stun:://google.com"]}]},
    media_stream_constraints={"video": True, "audio": False}
)

# Проверка дали е открит баркод по време на стрийминга
if ctx.video_processor and ctx.video_processor.detected_barcode:
    st.session_state.barcode = ctx.video_processor.detected_barcode

# Алтернативен метод: Ръчно въвеждане (за лесно тестване)
manual_barcode = st.text_input("Или въведете баркод ръчно за тест (напр. 4000175123456 или 8410012345678):")
if manual_barcode:
    st.session_state.barcode = manual_barcode

# СЕКЦИЯ 3: Резултати и Анализ
if st.session_state.barcode:
    barcode = st.session_state.barcode
    st.markdown("---")
    st.header("📊 Резултати от анализа")
    
    if barcode not in PRODUCTS_DB:
        # Генериране на автоматичен "непознат" продукт, за да работи с абсолютно всеки баркод
        product = {
            "name": f"Непознат продукт (Код: {barcode})",
            "ingredients": ["захар", "палмово масло", "вода"]
        }
    else:
        product = PRODUCTS_DB[barcode]

    st.subheader(f"📦 Продукт: {product['name']}")
    st.write(f"🔢 Баркод: **{barcode}**")

    critical_warnings = []
    harmful_ingredients = []
    safe_ingredients = []

    # Анализиране на съставките спрямо избора на потребителя
    for ing in product["ingredients"]:
        info = INGREDIENTS_INFO.get(ing, {"harmful": False, "desc": "Няма подробно описание в базата данни.", "triggers": []})
        
        # Проверка за конфликт със здравето
        is_critical = False
        for trigger in info["triggers"]:
            if trigger in selected_issues:
                critical_warnings.append((ing, trigger, info["desc"]))
                is_critical = True
        
        if not is_critical:
            if info["harmful"]:
                harmful_ingredients.append((ing, info["desc"]))
            else:
                safe_ingredients.append((ing, info["desc"]))

    # 1. Показване на Критични заплахи за здравето
    if critical_warnings:
        st.markdown("### 🛑 КРИТИЧНО ЗА ТВОЕТО ЗДРАВЕ:")
        for ing, trigger, desc in critical_warnings:
            st.markdown(f"""
            <div class='critical-box'>
                ⚠️ СЪСТАВКА: {ing.upper()}<br>
                Опасна за Вашето състояние: {trigger}!<br>
                <span style='font-weight:normal; font-size:16px;'>Об coronation: {desc}</span>
            </div>
            """, unsafe_allow_html=True)

    # 2. Показване на Общо вредни съставки
    if harmful_ingredients:
        st.markdown("### ⚠️ ВРЕДНИ СЪСТАВКИ (Обща вреда):")
        for ing, desc in harmful_ingredients:
            st.markdown(f"""
            <div class='harmful-box'>
                ⚫ <b>{ing.upper()}</b><br>
                <span style='font-size:16px;'>{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    # 3. Показване на Безопасни съставки
    if safe_ingredients:
        st.markdown("### ✅ БЕЗОПАСНИ СЪСТАВКИ:")
        for ing, desc in safe_ingredients:
            st.markdown(f"""
            <div class='safe-box'>
                🟢 <b>{ing.upper()}</b><br>
                <span style='font-size:16px;'>{desc}</span>
            </div>
            """, unsafe_allow_html=True)
            
    if not critical_warnings and not harmful_ingredients:
        st.success("🎉 Продуктът изглежда напълно безопасен спрямо вашите филтри!")
