import streamlit as st
from PIL import Image, ImageEnhance
import easyocr
import numpy as np
import re

# ========================= НАСТРОЙКИ =========================
st.set_page_config(
    page_title="AI Химия на Храните", 
    layout="centered", 
    page_icon="🥗"
)

st.title("🥗 AI Сканер на Етикети")
st.markdown("**Качете снимка → Анализ + Препоръки според Вашето здраве**")

# ====================== БАЗА ДАННИ ======================
harmful_dict = {
    "E250": "Натриев нитрит", 
    "E251": "Натриев нитрат",
    "E621": "Мононатриев глутамат (MSG)",
    "E407": "Карагенан", 
    "E450": "Дифосфати", 
    "E452": "Полифосфати",
    "E211": "Натриев бензоат",
    "E102": "Тартразин", 
    "E110": "Сънсет Жълто",
    "E952": "Цикламат",
}

keywords_harmful = {
    "палмово масло": "Палмово масло", 
    "palm oil": "Palm oil",
    "нитрит": "Нитрити", 
    "нитрат": "Нитрати",
    "фосфат": "Фосфати", 
    "хидрогенирано": "Хидрогенирани мазнини",
    "лактоза": "Лактоза", 
    "глутен": "Глутен"
}

# ====================== ПРЕПОРЪКИ ======================
condition_recommendations = {
    "Диабет": "Избягвайте подсладители, захар и глюкозен сироп. Предпочитайте нискогликемични продукти.",
    "Високо кръвно налягане / Сърдечни проблеми": "Ограничете натрий, нитрити и преработени меса.",
    "Бъбречни проблеми": "Внимавайте с фосфати (E450, E452) и преработени храни.",
    "Стомашно-чревни проблеми (колит, IBS, Crohn)": "Избягвайте карагенан (E407) и някои стабилизатори.",
    "Целиакия / Непоносимост към глутен": "Търсете продукти без глутен.",
    "Непоносимост към лактоза": "Избягвайте лактоза или избирайте безлактозни продукти.",
    "Аллергии / Астма": "Внимавайте с изкуствени оцветители и консерванти.",
    "Деца / Хиперактивност": "Избягвайте изкуствени оцветители и MSG."
}

# ====================== ФУНКЦИИ ======================
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

# ====================== ИНТЕРФЕЙС ======================

st.subheader("🧬 Вашето здравословно състояние")
selected_conditions = st.multiselect(
    "Изберете всички състояния, които се отнасят за Вас:",
    options=list(condition_recommendations.keys()),
    default=[],
    help="Можете да изберете повече от едно"
)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("Качете снимка на етикет", type=['jpg', 'jpeg', 'png'])
with col2:
    camera = st.camera_input("Направете снимка с камера")

image = None
if camera:
    image = Image.open(camera)
elif uploaded:
    image = Image.open(uploaded)

if image:
    # Поправено: use_column_width → width
    st.image(image, caption="Изображение за анализ", width=700)
    
    if st.button("🔍 Анализирай етикета и дай препоръки", 
                 type="primary", 
                 use_container_width=True):
        
        with st.spinner("Обработвам изображението с OCR..."):
            processed = preprocess_image(image)
            text = extract_text(processed)
            
            harmful = find_harmful(text)
            
            st.subheader("📝 Разпознат текст")
            st.write(text[:800] + "..." if len(text) > 800 else text)
            
            st.subheader("⚠️ Открити рискови съставки")
            if harmful:
                for code, desc in harmful:
                    st.error(f"**{code}** — {desc}")
            else:
                st.success("Не са открити рискови добавки от нашата база.")

            st.subheader("🧠 Персонализирани препоръки")
            if selected_conditions:
                st.info(f"**Избрани състояния:** {', '.join(selected_conditions)}")
            
            for cond in selected_conditions:
                st.warning(f"**{cond}**: {condition_recommendations[cond]}")
            
            if harmful:
                st.info("**Съвет:** По-добре ограничете или заменете този продукт.")
            else:
                st.success("Продуктът изглежда относително безопасен.")

            # Отчет
            report = f"""AI Анализ на хранителен етикет

Избрани заболявания: {selected_conditions}
Открити рискови съставки: {[item[0] for item in harmful]}
"""
            st.download_button(
                label="📥 Изтегли отчет",
                data=report,
                file_name="анализ_на_етикет.txt",
                mime="text/plain"
            )

# Допълнителна информация
with st.expander("📚 Списък с рискови добавки"):
    for k, v in harmful_dict.items():
        st.markdown(f"**{k}** — {v}")
 
 
