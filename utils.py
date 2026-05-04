import html
import requests
from database import get_all_users

async def broadcast_order(text, bot_token):
    users = get_all_users()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    if not users:
        print("[!] Рассылка невозможна: в базе нет активных пользователей.")
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
        except:
            pass
    
    print(f"[SENT] Заказ успешно разослан пользователям (всего: {len(users)})")

def format_notification(username, msg_link, text):
    if username:
        user_link = f"https://t.me/{username}"
        client_display = f"<a href='{user_link}'>@{username}</a>"
    else:
        client_display = f"<a href='{msg_link}'>[Профиль скрыт — перейти к сообщению в чате]</a>"

    clean_text = html.escape(text or "")
    
    return (
        f"<b>🚀 НОВЫЙ ЗАКАЗ</b>\n\n"
        f"👤 <b>Клиент:</b> {client_display}\n"
        f"__________________________\n\n"
        f"{clean_text}"
    )