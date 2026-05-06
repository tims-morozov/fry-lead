import sqlite3
import requests
import html
from config import CATEGORIES

def get_user_categories(user_id):
    """Извлекает текущий список ID категорий пользователя из базы данных[cite: 1]."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT categories FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return [c for c in (row[0].split(',') if row and row[0] else []) if c]

def get_categories_markup(user_id):
    """Формирует клавиатуру с динамическими галочками.
    Галочка на 'ВСЕ КАТЕГОРИИ' ставится только если выбраны все пункты[cite: 1].
    """
    user_cats = get_user_categories(user_id)
    all_cat_keys = list(CATEGORIES.keys())
    
    # Проверка: выбраны ли абсолютно все категории[cite: 1]
    is_all_selected = set(all_cat_keys).issubset(set(user_cats))
    all_status = "✅ " if is_all_selected else ""
    
    keyboard = []
    # Кнопка 'ВСЕ КАТЕГОРИИ'[cite: 1]
    keyboard.append([{"text": f"{all_status}ВСЕ КАТЕГОРИИ", "callback_data": "all_on"}])
    
    row_buttons = []
    for cat_id, info in CATEGORIES.items():
        # Определяем название категории (например, 'Конструкторы сайтов')[cite: 1]
        status = "✅ " if cat_id in user_cats else ""
        row_buttons.append({"text": f"{status}{info['name']}", "callback_data": f"toggle_{cat_id}"})
        
        # Группируем кнопки по 2 в ряд[cite: 1]
        if len(row_buttons) == 2:
            keyboard.append(row_buttons)
            row_buttons = []
            
    if row_buttons:
        keyboard.append(row_buttons)

    # Кнопка подтверждения без галочки[cite: 1]
    keyboard.append([{"text": "Подтвердить выбор", "callback_data": "confirm_settings"}])
    
    return {"inline_keyboard": keyboard}

def toggle_user_category(user_id, action):
    """Логика переключения:
    - Если выбраны ВСЕ, клик по одной категории снимает галочки с остальных.
    - В остальных случаях работает как обычный переключатель[cite: 1].
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    all_cat_keys = list(CATEGORIES.keys())
    
    if action == "all_on":
        # Принудительно выбираем всё[cite: 1]
        new_cats_list = all_cat_keys
    else:
        current_cats = get_user_categories(user_id)
        
        # Если сейчас активен режим 'ВСЕ КАТЕГОРИИ', то клик по любой кнопке 
        # оставляет только эту выбранную категорию[cite: 1]
        if set(all_cat_keys).issubset(set(current_cats)):
            new_cats_list = [action]
        else:
            # Обычный toggle (добавить/удалить)[cite: 1]
            if action in current_cats:
                current_cats.remove(action)
            else:
                current_cats.append(action)
            new_cats_list = current_cats
            
    new_cats_str = ",".join(new_cats_list)
    cursor.execute("UPDATE users SET categories = ? WHERE user_id = ?", (new_cats_str, user_id))
    conn.commit()
    conn.close()
    return get_categories_markup(user_id)

def format_notification(username, msg_link, text, category_id):
    """Форматирует уведомление с увеличенными отступами в шапке (как на скриншоте)[cite: 1]."""
    category_name = CATEGORIES.get(category_id, {}).get("name", category_id)
    
    # Ссылка на клиента или на сообщение, если профиль скрыт[cite: 1]
    client_display = f"<a href='https://t.me/{username}'>@{username}</a>" if username else f"<a href='{msg_link}'>Профиль скрыт - перейти к сообщению</a>"
    
    # Экранируем спецсимволы в тексте заказа[cite: 1]
    clean_text = html.escape(text or "")
    
    # Формируем структуру с визуальными пропусками строк[cite: 1]
    return (
        f"<b>🚀 НОВЫЙ ЗАКАЗ</b>\n\n"        # Отступ после заголовка
        f"📁 <b>Категория:</b> {category_name}\n\n"  # Отступ перед клиентом
        f"👤 <b>Клиент:</b> {client_display}\n"
        f"__________________________\n\n"   # Отступ перед телом сообщения
        f"{clean_text}"
    )

async def broadcast_order(text, category_id, bot_token):
    """Рассылает сообщение пользователям, у которых выбрана данная категория[cite: 1]."""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, categories FROM users")
    users = cursor.fetchall()
    conn.close()
    
    for u_id, u_cats in users:
        if u_cats and category_id in u_cats.split(','):
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={
                "chat_id": u_id, 
                "text": text, 
                "parse_mode": "HTML", 
                "disable_web_page_preview": True
            })

def classify_message(text):
    """Определяет категорию, учитывая количество совпадений и их вес (weight)."""
    text = text.lower()
    
    # 1. Глобальный фильтр стоп-слов
    from config import GLOBAL_STOP_WORDS
    if any(word.lower() in text for word in GLOBAL_STOP_WORDS):
        return None 

    best_category = None
    max_final_score = 0

    # 2. Поиск с учетом весов
    for cat_id, info in CATEGORIES.items():
        keywords = info.get('keywords', [])
        weight = info.get('weight', 1.0)
        
        matches = sum(1 for word in keywords if word in text)
        
        # Дополнительный бонус за уникальные технические термины[cite: 4]
        if cat_id == "TWA" and ("twa" in text or "webapp" in text):
            matches += 1 

        final_score = matches * weight
        
        if final_score > max_final_score:
            max_final_score = final_score
            best_category = cat_id

    if max_final_score == 0:
        return None

    return best_category