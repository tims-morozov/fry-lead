import html
import requests
import re
from database import get_all_users
from config import CATEGORIES, GLOBAL_STOP_WORDS, ORDER_MARKERS

async def broadcast_order(text, bot_token):
    """Рассылка сообщения всем зарегистрированным пользователям бота"""
    users = get_all_users()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if not users:
        return

    for user_id in users:
        payload = {
            "chat_id": user_id, 
            "text": text, 
            "parse_mode": "HTML", 
            "disable_web_page_preview": True
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"Ошибка рассылки для {user_id}: {e}")

def classify_message(text):
    """Логика фильтрации и определения категории заказа"""
    text = text.lower()
    
    # 1. Сначала проверяем глобальные стоп-слова
    if any(stop in text for stop in GLOBAL_STOP_WORDS):
        return None

    # 2. Проверяем наличие маркеров заказа или вакансии
    if not any(marker in text for marker in ORDER_MARKERS):
        return None

    scores = {}
    for cat_id, data in CATEGORIES.items():
        current_score = 0
        for word in data["keywords"]:
            pattern = r'\b' + re.escape(word.strip())
            if re.search(pattern, text):
                current_score += data["weight"]
        
        # Если набрано достаточно веса для категории
        if current_score >= 1.0:
            scores[cat_id] = current_score

    if scores:
        return max(scores, key=scores.get)
    
    return None

def format_notification(username, msg_link, text, category_id):
    """Форматирование уведомления с отступами и расширенной ссылкой на скрытый профиль"""
    category_name = CATEGORIES[category_id]["name"]
    
    # Логика отображения клиента: никнейм или ссылка на сообщение, если профиль скрыт
    if username:
        client_display = f"<a href='https://t.me/{username}'>@{username}</a>"
    else:
        client_display = f"<a href='{msg_link}'>Профиль скрыт — перейти к сообщению</a>"
        
    clean_text = html.escape(text or "")
    
    return (
        f"<b>🚀 НОВЫЙ ЗАКАЗ / ВАКАНСИЯ</b>\n\n"
        f"📁 <b>Категория:</b> #{category_id} ({category_name})\n\n"
        f"👤 <b>Клиент:</b> {client_display}\n"
        f"__________________________\n\n"
        f"{clean_text}"
    )