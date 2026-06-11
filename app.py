import cv2
from pyzbar import pyzbar
import requests
import re

# 1. Основна база данни със съставки
E_ADDITIVES = {
    "E100": {"name": "Куркумин", "group": "Зелена (Безопасна)", "desc": "Естествен жълт оцветител от куркума."},
    "E300": {"name": "Аскорбинова киселина", "group": "Зелена (Безопасна)", "desc": "Чист Витамин С. Спира развалянето."},
    "E322": {"name": "Лецитин", "group": "Зелена (Безопасна)", "desc": "Естествен емулгатор от соя или яйца."},
    "E621": {"name": "Мононатриев глутамат", "group": "Жълта (Умерено вредна)", "desc": "Овкусител. Може да причини главоболие при чувствителност."},
    "E407": {"name": "Карагенан", "group": "Жълта (Умерено вредна)", "desc": "Сгъстител. Може да раздразни червата."},
    "E250": {"name": "Натриев нитрит", "group": "Червена (Опасна)", "desc": "Консервант за меса. Свързва се с канцерогенни нитрозамини."},
    "E951": {"name": "Аспартам", "group": "Червена (Опасна)", "desc": "Изкуствен подсладител. Възможно канцерогенен според СЗО."},
    "E102": {"name": "Тартразин", "group": "Червена (Опасна)", "desc": "Азооцветител. Засилва хиперактивността при децата."}
}

# 2. Функция за анализ и извеждане на съставките
def analyze_ingredients(ingredients_text):
    print("\n" + "="*40)
    print("📋 РЕЗУЛТАТИ ОТ АНАЛИЗА НА СЪСТАВКИТЕ:")
    print("="*40)
    
    found_codes = re.findall(r'[EeЕе]\s*\d{3,4}[a-zA-Zа-яА-Я]?', ingredients_text)
    cleaned_codes = list(set([code.replace(' ', '').upper().replace('Е', 'E') for code in found_codes]))
    
    if not cleaned_codes:
        print("❌ Не бяха открити Е-номера в текста на този продукт.")
        print(f"Пълен текст на състава: {ingredients_text[:200]}...")
        return

    for code in cleaned_codes:
        if code in E_ADDITIVES:
            info = E_ADDITIVES[code]
            print(f"🔹 [{code}] {info['name']}")
            print(f"   Категория: {info['group']}")
            print(f"   Ефект: {info['desc']}")
        else:
            print(f"❓ [{code}] Разрешена съставка, липсваща в локалния списък на чата.")
        print("-" * 40)

# 3. Функция за вземане на състава по баркод (Използва безплатното API на Open Food Facts)
def fetch_product_by_barcode(barcode):
    print(f"\n🔍 Търсене в базата данни за баркод: {barcode}...")
    url = f"https://openfoodfacts.org{barcode}.json"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == 1:
                product = data["product"]
                product_name = product.get("product_name", "Неизвестен продукт")
                ingredients_text = product.get("ingredients_text", "")
                
                print(f"🛒 Намерен продукт: {product_name}")
                if ingredients_text:
                    analyze_ingredients(ingredients_text)
                else:
                    # Ако няма цял текст, проверяваме списъка с добавки директно от API-то
                    additives = product.get("ingredients_tags", [])
                    print(f"Открити добавки: {', '.join(additives)}")
                    # Преобразуваме таговете в чист текст за функцията за анализ
                    analyze_ingredients(" ".join(additives))
            else:
                print("❌ Продуктът не е намерен в световната база данни.")
        else:
            print("❌ Грешка при връзката с базата данни.")
    except Exception as e:
        print(f"❌ Проблем с мрежата: {e}")

# 4. Функция за сканиране на баркод с камера
def scan_barcode_with_camera():
    print("\n🎥 Стартиране на камерата... Насочете баркода на продукта към нея.")
    print("Натиснете бутона 'q' на клавиатурата, за да затворите камерата.")
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Неуспешен достъп до камерата.")
            break
            
        # Търсене на баркодове в текущия кадър
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            # Рисуване на рамка около баркода на екрана
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            if barcode_data:
                cap.release()
                cv2.destroyAllWindows()
                return barcode_data
                
        cv2.imshow("Barcode Scanner (Press 'q' to exit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    return None

# 5. Главен интерфейс за управление
def main():
    print("=========================================")
    print("   АНАЛИЗАТОР НА СЪСТАВКИ И Е-НОМЕРА    ")
    print("=========================================")
    print("1. Ръчно въвеждане на баркод (цифри)")
    print("2. Сканиране на баркод с КАМЕРА")
    print("3. Директно въвеждане на текст от етикет")
    
    choice = input("\nИзберете опция (1, 2 или 3): ").strip()
    
    if choice == "1":
        barcode = input("Въведете цифрите на баркода: ").strip()
        fetch_product_by_barcode(barcode)
    elif choice == "2":
        barcode = scan_barcode_with_camera()
        if barcode:
            fetch_product_by_barcode(barcode)
        else:
            print("❌ Сканирането беше прекратено или не бе открит баркод.")
    elif choice == "3":
        text = input("Поставете или напишете съставките от етикета тук:\n")
        analyze_ingredients(text)
    else:
        print("❌ Невалиден избор. Моля, стартирайте програмата отново.")

if __name__ == "__main__":
    main()
