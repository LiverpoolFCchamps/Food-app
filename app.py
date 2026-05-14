import streamlit as st
from PIL import Image, ImageEnhance
import easyocr
import numpy as np
import re
from deep_translator import GoogleTranslator

st.set_page_config(page_title="AI Сканер на Етикети", layout="wide", page_icon="🥗")

st.title("🥗 AI Сканер на Етикети - Многоезичен")
st.markdown("**Поддържа много езици + превод на етикета**")

# ====================== НАСТРОЙКИ ======================
languages = {
    'bg': 'Български',
    'en': 'English',
    'ru': 'Русский',
    'de': 'Deutsch',
    'fr': 'Français',
    'es': 'Español',
    'tr': 'Türkçe'
}

# ====================== БАЗА ДАННИ ======================
harmful_dict = {
    "E250": "Натриев нитрит", "E251": "Натриев нитрат", "E621": "Мононатриев глутамат",
    "E407": "Карагенан", "E450": "Дифосфати", "E211": "Натриев бензоат",
    "E102": "Тартразин", "E110": "Сънсет Жълто"
}

condition_recommendations = {
    "Диабет": "Избягвайте захар и подсладители.",
    "Високо кръвно": "Ограничете сол и преработени меса.",
    "Бъбречни проблеми": "Внимавайте с фосфати.",
    "Непоносимост към лактоза": "Избягвайте лактоза.",
}

# ====================== ФУНКЦИИ ======================
def preprocess_image(image):
    img = ImageEnhance.Contrast(image).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = ImageEnhance.Brightness(img).enhance(1.2)
    return img.convert('L')

@st.cache_resource
def get_reader(lang_list):
    return easyocr.Reader(lang_list, gpu=False)

def extract_text(image, lang_list=['bg', 'en']):
    reader = get_reader(lang_list)
    results = reader.readtext(np.array(image), detail=0)
    return " ".join(results).strip()

def translate_text(text, target_lang='bg'):
    if not text:
        return "Няма текст за превод."
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except:
        return "Грешка при превода. Опитайте отново."

# ====================== ИНТЕРФЕЙС ======================
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📸 Качване на етикет")
    uploaded = st.file_uploader("Качете снимка на етикет", type=['jpg', 'jpeg', 'png'])
    camera = st.camera_input("Или направете снимка")

with col2:
    st.subheader("🌐 Езици за разпознаване")
    selected_langs = st.multiselect(
        "Изберете езици за OCR",
        options=list(languages.keys()),
        default=['bg', 'en'],
        format_func=lambda x: languages[x]
    )

st.markdown("---")

image = None
if camera:
    image = Image.open(camera)
elif uploaded:
    image = Image.open(uploaded)

if image:
    st.image(image, caption="Изображение за анализ", use_column_width=True)
    
    if st.button("🔍 Разпознай текст", type="primary", use_container_width=True):
        with st.spinner("Разпознаване на текст..."):
            processed_img = preprocess_image(image)
            raw_text = extract_text(processed_img, selected_langs)
            
            st.subheader("📝 Разпознат оригинален текст")
            st.write(raw_text if raw_text else "Не беше разпознат текст.")

            # === ПРЕВОД ===
            st.subheader("🌐 Превод на етикета")
            target = st.selectbox("Преведи към:", 
                                options=['bg', 'en', 'de', 'ru'], 
                                format_func=lambda x: languages.get(x, x))
            
            if st.button("Преведи текста"):
                with st.spinner("Превеждам..."):
                    translated = translate_text(raw_text, target)
                    st.success("**Превод:**")
                    st.write(translated)

            # === АНАЛИЗ ===
            harmful = []
            e_matches = re.findall(r'e?\s*(\d{3,4}[a-z]?)', raw_text.lower())
            for e in e_matches:
                code = "E" + e.upper() if not e.upper().startswith("E") else e.upper()
                if code in harmful_dict:
                    harmful.append((code, harmful_dict[code]))

            st.subheader("⚠️ Открити рискови съставки")
            if harmful:
                for code, desc in harmful:
                    st.error(f"**{code}** — {desc}")
            else:
                st.success("Не са открити рискови добавки от базата.")

# Допълнителна информация
with st.expander("📚 Рискови добавки и съвети"):
    for k, v in harmful_dict.items():
        st.markdown(f"**{k}** — {v}")
