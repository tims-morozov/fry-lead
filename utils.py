import html
import requests
import re
from database import get_all_users
from config import CATEGORIES, STOP_WORDS, ORDER_MARKERS

async def broadcast_order(text, bot_token):
    users = get_all_users()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    if not users: return

    for user_id in users:
        payload = {"chat_id": user_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        try: requests.post(url, json=payload, timeout=5)
        except: pass

def classify_message(text):
    text = text.lower()
    
    # 1. Если есть стоп-слова (реклама услуг) — сразу игнорируем
    if any(stop in text for stop in STOP_WORDS): 
        return None

    # 2. ПРОВЕРКА НА МАРКЕР ЗАКАЗА (Обязательно для отсева простого упоминания категорий)
    if not any(marker in text for marker in ORDER_MARKERS):
        return None

    scores = {}
    for cat_id, data in CATEGORIES.items():
        score = 0
        for word in data["keywords"]:
            pattern = r'\b' + re.escape(word.strip())
            if re.search(pattern, text):
                score += data["weight"]
        if score > 0: scores[cat_id] = score

    # 3. Если категория определена по ключам — возвращаем её
    if scores:
        return max(scores, key=scores.get)
    
    return None

def format_notification(username, msg_link, text, category_id):
    category_name = CATEGORIES[category_id]["name"]
    client_display = f"<a href='https://t.me/{username}'>@{username}</a>" if username else f"<a href='{msg_link}'>[Профиль скрыт]</a>"
    clean_text = html.escape(text or "")
    
    return (
        f"<b>🚀 НОВЫЙ ЗАКАЗ</b>\n"
        f"📁 <b>Категория:</b> #{category_id} ({category_name})\n"
        f"👤 <b>Клиент:</b> {client_display}\n"
        f"__________________________\n\n"
        f"{clean_text}"
    )