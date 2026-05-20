import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import cv2
from pyzbar.pyzbar import decode
import queue

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

# Използваме сигурна опашка (Queue) за прехвърляне на данните от камерата към Streamlit
result_queue = queue.Queue()

def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    barcodes = decode(img)
    
    for barcode in barcodes:
        code_str = barcode.data.decode('utf-8')
        # Когато открием баркод, го пращаме в опашката
        result_queue.put(code_str)
        # Рисуваме рамка
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

# Сигурно стартиране на уеб камерата с callback функция
rtc_configuration={"iceServers": [{"urls": ["stun:google.com:19302"]}]},

# Проверяваме дали в опашката има пристигнал баркод от камерата
scanned_barcode = None
try:
    scanned_barcode = result_queue.get_nowait()
except queue.Empty:
    scanned_barcode = None

# Алтернативен метод: Ръчно въвеждане (за лесно тестване, ако камерата няма фокус)
manual_barcode = st.text_input("Или въведете баркод ръчно за тест (напр. 4000175123456 или 8410012345678):")

# Избираме кой баркод да използваме
final_barcode = manual_barcode if manual_barcode else scanned_barcode

# СЕКЦИЯ 3: Резултати и Анализ
if final_barcode:
    st.markdown("---")
    st.header("📊 Резултати от анализа")
    
    if final_barcode not in PRODUCTS_DB:
        product = {
            "name": f"Непознат продукт (Код: {final_barcode})",
            "ingredients": ["захар", "палмово масло", "вода", "фосфорна киселина"]
        }
    else:
        product = PRODUCTS_DB[final_barcode]

    st.subheader(f"📦 Продукт: {product['name']}")
    st.write(f"🔢 Баркод: **{final_barcode}**")

    critical_warnings = []
    harmful_ingredients = []
    safe_ingredients = []

    for ing in product["ingredients"]:
        info = INGREDIENTS_INFO.get(ing, {"harmful": False, "desc": "Няма подробно описание в базата данни.", "triggers": []})
        
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

    # 1. Критични заплахи
    if critical_warnings:
        st.markdown("### 🛑 КРИТИЧНО ЗА ТВОЕТО ЗДРАВЕ:")
        for ing, trigger, desc in critical_warnings:
            st.markdown(f"""
            <div class='critical-box'>
                ⚠️ СЪСТАВКА: {ing.upper()}<br>
                Опасна за Вашето състояние: {trigger}!<br>
                <span style='font-weight:normal; font-size:16px;'>Описание: {desc}</span>
            </div>
            """, unsafe_allow_html=True)

    # 2. Вредни съставки
    if harmful_ingredients:
        st.markdown("### ⚠️ ВРЕДНИ СЪСТАВКИ (Обща вреда):")
        for ing, desc in harmful_ingredients:
            st.markdown(f"""
            <div class='harmful-box'>
                ⚫ <b>{ing.upper()}</b><br>
                <span style='font-size:16px;'>{desc}</span>
            </div>
            """, unsafe_allow_html=True)

    # 3. Безопасни съставки
    if safe_ingredients:
        st.markdown("### ✅ БЕЗОПАСНИ СЪСТАВКИ:")
        for ing, desc in safe_ingredients:
            st.markdown(f"""
            <div class='safe-box'>
                🟢 <b>{ing.upper()}</b><br>
                <span style='font-size:16px;'>{desc}</span>
            </div>
            """, unsafe_allow_html=True)
