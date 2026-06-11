import streamlit as st
import cv2
from pyzbar import pyzbar
import requests
import re
from PIL import Image
import numpy as np

# Локална база данни с Е-номера
E_ADDITIVES = {
    "E100": {"name": "Куркумин", "group": "🟢 Зелена (Безопасна)", "desc": "Естествен жълт оцветител от куркума."},
    "E300": {"name": "Аскорбинова киселина", "group": "🟢 Зелена (Безопасна)", "desc": "Чист Витамин С. Спира развалянето."},
    "E322": {"name": "Лецитин", "group": "🟢 Зелена (Безопасна)", "desc": "Естествен емулгатор от соя или яйца."},
    "E621": {"name": "Мононатриев глутамат", "group": "🟡 Жълта (Умерено вредна)", "desc": "Овкусител. Може да причини главоболие при чувствителност."},
    "E407": {"name": "Карагенан", "group": "🟡 Жълта (Умерено вредна)", "desc": "Сгъстител. Може да раздразни червата."},
    "E250": {"name": "Натриев нитрит", "group": "🔴 Червена (Опасна)", "desc": "Консервант за меса. Свързва се с канцерогенни нитрозамини."},
    "E951": {"name": "Аспартам", "group": "🔴 Червена (Опасна)", "desc": "Изкуствен подсладител. Възможно канцерогенен според СЗО."},
    "E102": {"name": "Тартразин", "group": "🔴 Червена (Опасна)", "desc": "Азооцветител. Засилва хиперактивността при децата."}
}

def analyze_ingredients(text):
    found_codes = re.findall(r'[EeЕе]\s*\d{3,4}[a-zA-Zа-яА-Я]?', text)
    cleaned_codes = list(set([code.replace(' ', '').upper().replace('Е', 'E') for code in found_codes]))
    
    if not cleaned_codes:
        st.warning("❌ Не бяха открити Е-номера в състава на този продукт.")
        return

    for code in cleaned_codes:
        if code in E_ADDITIVES:
            info = E_ADDITIVES[code]
            if "🔴" in info["group"]:
                st.error(f"**[{code}] {info['name']}**\n\n*Категория:* {info['group']}\n\n*Ефект:* {info['desc']}")
            elif "🟡" in info["group"]:
                st.warning(f"**[{code}] {info['name']}**\n\n*Категория:* {info['group']}\n\n*Ефект:* {info['desc']}")
            else:
                st.success(f"**[{code}] {info['name']}**\n\n*Категория:* {info['group']}\n\n*Ефект:* {info['desc']}")
        else:
            st.info(f"❓ **[{code}]** Разрешена съставка в ЕС, но липсва в базата данни на приложението.")

def fetch_product(barcode):
    url = f"https://openfoodfacts.org{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data["product"]
                st.subheader(f"🛒 Продукт: {product.get('product_name', 'Неизвестен')}")
                ingredients = product.get("ingredients_text", "")
                if not ingredients:
                    ingredients = " ".join(product.get("ingredients_tags", []))
                analyze_ingredients(ingredients)
            else:
                st.error("❌ Продуктът не е намерен в глобалната база данни.")
        else:
            st.error("❌ Грешка при връзката с базата данни за продукти.")
    except Exception as e:
        st.error(f"Грешка при връзка с API: {e}")

# Стриймлит Интерфейс
st.title("🛡️ Скенер за вредни съставки (Е-номера)")

option = st.radio("Изберете метод:", ["Камера (Баркод)", "Ръчен баркод", "Директен текст от етикет"])

if option == "Камера (Баркод)":
    st.info("Направете снимка на баркода с камерата си. Уверете се, че е добре осветен и на фокус.")
    image_data = st.camera_input("Снимай баркод")
    
    if image_data:
        img = Image.open(image_data)
        opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        barcodes = pyzbar.decode(opencv_img)
        
        if barcodes:
            barcode_value = barcodes.data.decode("utf-8")
            st.success(f"Успешно разчетен баркод: {barcode_value}")
            fetch_product(barcode_value)
        else:
            st.error("❌ Неуспешно разчитане. Моля, приближете или отдалечете баркода и опитайте с нова снимка.")

elif option == "Ръчен баркод":
    barcode_input = st.text_input("Въведете цифрите на баркода:")
    if st.button("Провери баркод") and barcode_input:
        fetch_product(barcode_input)

elif option == "Директен текст от етикет":
    text_input = st.text_area("Поставете текста със съставките тук (напр. съдържа Е250 и Е300):")
    if st.button("Анализирай текст") and text_input:
        analyze_ingredients(text_input)
