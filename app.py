import streamlit as st
from PIL import Image, ImageEnhance
import easyocr
import numpy as np
import re
from deep_translator import GoogleTranslator

st.set_page_config(page_title="AI Химия на Храните", layout="wide", page_icon="🥗")

st.title("🥗 AI Сканер на Етикети")
st.markdown("**Многоезичен анализ + Препоръки според здравето + Алтернативи**")

# ====================== БАЗА ДАННИ ======================
harmful_dict = {
    "E250": {"name": "Натриев нитрит", "risk": "Може да образува канцерогенни нитрозамини.", "alt": "Прясно месо, приготвено вкъщи"},
    "E251": {"name": "Натриев нитрат", "risk": "Подобно на E250, риск при честа консумация.", "alt": "Прясно месо"},
    "E621": {"name": "Мононатриев глутамат (MSG)", "risk": "Може да предизвика главоболие, сърцебиене при чувствителни хора.", "alt": "Естествени подправки и билки"},
    "E407": {"name": "Карагенан", "risk": "Може да предизвика възпаления в червата.", "alt": "Продукти без сгъстители"},
    "E450": {"name": "Дифосфати", "risk": "Може да наруши калциевия баланс и да натоварва бъбреците.", "alt": "Продукти с къс списък на съставките"},
    "E211": {"name": "Натриев бензоат", "risk": "Може да предизвика алергични реакции.", "alt": "Натурални консерванти (лимонена киселина)"},
    "E102": {"name": "Тартразин", "risk": "Изкуствен оцветител, свързан с хиперактивност.", "alt": "Продукти с естествени оцветители"},
}

condition_recommendations = {
    "Диабет": "Избягвайте захар, подсладители и високо въглехидратни продукти.",
    "Високо кръвно налягане": "Ограничете натрий, нитрити и преработени меса.",
    "Бъбречни проблеми": "Внимавайте с фосфати (E450, E452) и високо съдържание на калий.",
    "Стомашно-чревни проблеми": "Избягвайте карагенан (E407) и изкуствени добавки.",
    "Непоносимост към лактоза": "Търсете безлактозни продукти.",
    "Целиакия / Глутен": "Търсете 'Без глутен'.",
    "Аллергии": "Внимавайте с изкуствени оцветители и консерванти."
}

# ====================== ФУНКЦИИ ======================
def preprocess_image(image):
    img = ImageEnhance.Contrast(image).enhance(2.0)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = ImageEnhance.Brightness(img).enhance(1.3)
    return img.convert('L')

@st.cache_resource
def get_reader(langs):
    return easyocr.Reader(langs, gpu=False)

def extract_text(image, langs):
    reader = get_reader(langs)
    results = reader.readtext(np.array(image), detail=0)
    return " ".join(results).strip()

def translate_text(text, target='bg'):
    if not text:
        return ""
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except:
        return "Грешка при превода. Моля, опитайте отново."

# ====================== ИНТЕРФЕЙС ======================
st.sidebar.header("🧬 Вашето здраве")
selected_conditions = st.sidebar.multiselect(
    "Изберете вашите здравословни проблеми:",
    options=list(condition_recommendations.keys()),
    default=[]
)

st.sidebar.markdown("---")
st.sidebar.header("🌐 Настройки")
target_lang = st.sidebar.selectbox(
    "Превод на етикета към:",
    options=['bg', 'en', 'de', 'ru', 'tr'],
    format_func=lambda x: {"bg":"Български", "en":"English", "de":"German", "ru":"Russian", "tr":"Turkish"}[x]
)

# Главна част
col1, col2 = st.columns([3, 1])

with col1:
    uploaded = st.file_uploader("Качете снимка на етикет", type=['jpg', 'jpeg', 'png'])
with col2:
    camera = st.camera_input("Снимка с камера")

image = None
if camera:
    image = Image.open(camera)
elif uploaded:
    image = Image.open(uploaded)

if image:
    st.image(image, caption="Изображение", use_column_width=True)

    if st.button("🔍 Анализирай етикета", type="primary", use_container_width=True):
        with st.spinner("Разпознаване на текст..."):
            processed = preprocess_image(image)
            raw_text = extract_text(processed, ['bg', 'en', 'ru', 'de', 'fr', 'es', 'tr'])
            
            # === РАЗПОЗНАТ ТЕКСТ ===
            st.subheader("📝 Разпознат текст")
            st.write(raw_text if raw_text else "Текстът не беше разпознат.")

            # === ПРЕВОД ===
            st.subheader("🌐 Превод")
            translated = translate_text(raw_text, target_lang)
            st.write(translated)

            # === ВРЕДНИ СЪСТАВКИ ===
            harmful_found = []
            e_matches = re.findall(r'e?\s*(\d{3,4}[a-z]?)', raw_text.lower())
            for e in e_matches:
                code = "E" + e.upper() if not e.upper().startswith("E") else e.upper()
                if code in harmful_dict:
                    harmful_found.append(code)

            st.subheader("⚠️ Открити рискови съставки")
            if harmful_found:
                for code in harmful_found:
                    info = harmful_dict[code]
                    st.error(f"**{code} — {info['name']}**")
                    st.write(f"Риск: {info['risk']}")
                    st.write(f"Заместител: {info['alt']}")
            else:
                st.success("Не са открити рискови добавки от нашата база.")

            # === ПЕРСОНАЛИЗИРАНИ ПРЕПОРЪКИ ===
            st.subheader("🧠 Персонализирани препоръки")
            if selected_conditions:
                for cond in selected_conditions:
                    st.warning(f"**{cond}**: {condition_recommendations[cond]}")
            else:
                st.info("Не сте избрали здравословни проблеми.")

            # === АЛТЕРНАТИВИ НА ПРОДУКТА ===
            st.subheader("🌱 По-здравословни алтернативи на продукта")
            st.info("""
            • Вместо колбаси и шунки → Печено пилешко/свинско филе с подправки  
            • Вместо чипс → Домашни печени зеленчуци или ядки  
            • Вместо сладки напитки → Вода с лимон и мента  
            • Вместо индустриални сладкиши → Домашни десерти с естествени съставки
            """)

            # Изтегляне на отчет
            report = f"""Анализ на етикет
Разпознат текст: {raw_text}
Превод: {translated}
Открити рискови: {harmful_found}
Здравословни проблеми: {selected_conditions}
"""
            st.download_button("📥 Изтегли пълен отчет", report, "етикет_анализ.txt")

# Допълнителна информация
with st.expander("📚 Подробна информация за добавките"):
    for code, info in harmful_dict.items():
        st.markdown(f"**{code} — {info['name']}**")
        st.write(f"Риск: {info['risk']}")
        st.write(f"Заместител: {info['alt']}")
        st.markdown("---")
