import streamlit as st
from PIL import Image, ImageEnhance
import easyocr
import numpy as np
import re

st.set_page_config(page_title="AI Химия на Храните", layout="centered", page_icon="🥗")

st.title("🥗 AI Сканер на Етикети")
st.markdown("**Качете снимка на етикет → Получете анализ + персонализирани препоръки според здравето ви**")

# ====================== БАЗА ДАННИ ======================
harmful_dict = {
    "E250": "Натриев нитрит", "E251": "Натриев нитрат",
    "E621": "Мононатриев глутамат (MSG)",
    "E407": "Карагенан", 
    "E450": "Дифосфати", "E452": "Полифосфати",
    "E211": "Натриев бензоат",
    "E102": "Тартразин", "E110": "Сънсет Жълто",
    "E952": "Цикламат",
}

keywords_harmful = {
    "палмово масло": "Палмово масло", "palm oil": "Palm oil",
    "нитрит": "Нитрити", "нитрат": "Нитрати",
    "фосфат": "Фосфати", "хидрогенирано": "Хидрогенирани мазнини",
    "лактоза": "Лактоза", "глутен": "Глутен"
}

# ====================== ПРЕПОРЪКИ ПО ЗАБОЛЯВАНИЯ ======================
condition_recommendations = {
    "Диабет": "Избягвайте подсладители, захар, глюкозен сироп. Предпочитайте нискогликемични продукти.",
    "Високо кръвно налягане / Сърдечни проблеми": "Ограничете натрий, нитрити и преработени меса.",
    "Бъбречни проблеми": "Внимавайте с фосфати (E450, E452), калий и преработени храни.",
    "Стомашно-чревни проблеми (колит, IBS, Crohn)": "Избягвайте карагенан (E407) и някои стабилизатори.",
    "Целиакия / Непоносимост към глутен": "Търсете продукти без глутен.",
    "Непоносимост към лактоза": "Избягвайте лактоза или избирайте безлактозни продукти.",
    "Аллергии / Астма": "Внимавайте с изкуствени оцветители (E102, E110 и др.) и консерванти.",
    "Деца / Хиперактивност": "Избягвайте изкуствени оцветители и MSG."
}

# ==================== OCR ФУНКЦИИ ====================
def preprocess_image(image):
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    return image.convert('L')

def extract_text(image):
    reader = easyocr.Reader(['bg', 'en'], gpu=False)
    results = reader.readtext(np.array(image), detail=0)
    return " ".join(results).lower()

def find_harmful(text):
    found = []
    e_matches = re.findall(r'e?\s*(\d{3,4}[a-z]?)', text)
    for e in e_matches:
        e_code = "E" + e.upper() if not e.upper().startswith("E") else e.upper()
        if e_code in harmful_dict:
            found.append((e_code, harmful_dict[e_code]))
    
    for kw, name in keywords_harmful.items():
        if kw in text:
            found.append((name, "Потенциално проблемна"))
    return list(set(found))

# ==================== ИНТЕРФЕЙС ====================

# === Попитване за заболявания (много видно) ===
st.subheader("🧬 Здравословно състояние")
selected_conditions = st.multiselect(
    "Изберете всички състояния, които се отнасят за Вас (можете да изберете няколко):",
    options=list(condition_recommendations.keys()),
    default=[],
    help="Изборът на повече от едно заболяване ще направи препоръките по-точни."
)

st.markdown("---")

# === Основна част ===
col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("Качете снимка на етикет", type=['jpg', 'jpeg', 'png'])
with col2:
    camera = st.camera_input("Направете нова снимка с камера")

image = None
if camera:
    image = Image.open(camera)
elif uploaded:
    image = Image.open(uploaded)

if image:
    st.image(image, caption="Изображение за анализ", use_column_width=True)
    
    if st.button("🔍 Анализирай етикета и дай препоръки", type="primary", size="large"):
        with st.spinner("Обработвам изображението..."):
            processed = preprocess_image(image)
            text = extract_text(processed)
            
            harmful = find_harmful(text)
            
            # Показване на резултатите
            st.subheader("📝 Разпознат текст")
            st.write(text[:800] + "..." if len(text) > 800 else text)
            
            st.subheader("⚠️ Открити рискови съставки")
            if harmful:
                for code, desc in harmful:
                    st.error(f"**{code}** — {desc}")
            else:
                st.success("Не са открити рискови добавки от нашата база.")

            # === Персонализирани препоръки ===
            st.subheader("🧠 Персонализирани препоръки според Вашето здраве")
            
            if selected_conditions:
                st.info(f"**Избрани състояния:** {', '.join(selected_conditions)}")
            
            for cond in selected_conditions:
                st.warning(f"**{cond}**: {condition_recommendations[cond]}")
            
            # Общи препоръки
            if harmful:
                st.info("**Обща препоръка:** Ограничете консумацията на този продукт или го заменете с по-натурален вариант.")
            else:
                st.success("Продуктът изглежда приемлив, но винаги четете етикета!")

            # Изтегляне на отчет
            report = f"""AI Анализ на хранителен етикет
Избрани заболявания: {selected_conditions}
Открити съставки: {harmful}
"""
            st.download_button("📥 Изтегли пълен отчет", report, "food_analysis_report.txt", mime="text/plain")

# Информация в отделен таб
with st.expander("📚 Виж списък с рискови добавки"):
    for k, v in harmful_dict.items():
        st.markdown(f"**{k}** — {v}")
