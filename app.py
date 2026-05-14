import streamlit as st
from PIL import Image, ImageEnhance
import easyocr
import numpy as np
import re

st.set_page_config(page_title="AI Сканер на Етикети", layout="centered", page_icon="🥗")

st.title("🥗 AI Сканер на Етикети")
st.markdown("**Качете снимка → Анализ + Препоръки**")

# ====================== БАЗИ ======================
harmful_dict = {
    "E250": "Натриев нитрит", "E251": "Натриев нитрат", "E621": "Мононатриев глутамат",
    "E407": "Карагенан", "E450": "Дифосфати", "E211": "Натриев бензоат",
}

keywords_harmful = {"палмово масло": "Палмово масло", "нитрит": "Нитрити", "лактоза": "Лактоза"}

condition_recommendations = {
    "Диабет": "Избягвайте захар и подсладители.",
    "Високо кръвно": "Ограничете сол и преработени меса.",
    "Бъбречни проблеми": "Внимавайте с фосфати.",
    "Непоносимост към лактоза": "Избягвайте лактоза.",
}

# ====================== ФУНКЦИИ ======================
def preprocess_image(image):
    img = ImageEnhance.Contrast(image).enhance(1.8)
    img = ImageEnhance.Sharpness(img).enhance(1.8)
    return img.convert('L')

def extract_text(image):
    reader = easyocr.Reader(['bg', 'en'], gpu=False)
    results = reader.readtext(np.array(image), detail=0)
    return " ".join(results).lower()

def find_harmful(text):
    found = []
    e_matches = re.findall(r'e?\s*(\d{3,4}[a-z]?)', text)
    for e in e_matches:
        code = "E" + e.upper() if not e.upper().startswith("E") else e.upper()
        if code in harmful_dict:
            found.append((code, harmful_dict[code]))
    for kw, name in keywords_harmful.items():
        if kw in text:
            found.append((name, "Потенциално проблемна"))
    return list(set(found))

# ====================== ИНТЕРФЕЙС ======================
st.subheader("🧬 Здравословно състояние")
selected_conditions = st.multiselect(
    "Изберете вашите състояния (може няколко):",
    options=list(condition_recommendations.keys()),
    default=[]
)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("Качете снимка", type=['jpg', 'jpeg', 'png'])
with col2:
    camera = st.camera_input("Снимка с камера")

image = None
if camera:
    image = Image.open(camera)
elif uploaded:
    image = Image.open(uploaded)

if image:
    st.image(image, caption="Изображение за анализ", use_column_width=True)
    
    if st.button("🔍 Анализирай етикета", type="primary", use_container_width=True):
        with st.spinner("Извличам текст..."):
            processed = preprocess_image(image)
            text = extract_text(processed)
            
            harmful = find_harmful(text)
            
            st.subheader("📝 Разпознат текст")
            st.write(text[:700] + "..." if len(text) > 700 else text)
            
            st.subheader("⚠️ Открити рискови съставки")
            if harmful:
                for code, desc in harmful:
                    st.error(f"**{code}** — {desc}")
            else:
                st.success("Не са открити рискови добавки.")

            st.subheader("🧠 Препоръки")
            if selected_conditions:
                for cond in selected_conditions:
                    st.warning(f"**{cond}**: {condition_recommendations[cond]}")
            else:
                st.info("Няма избрани здравословни проблеми.")

# expander
with st.expander("Списък на рискови добавки"):
    for k, v in harmful_dict.items():
        st.write(f"**{k}** — {v}")
