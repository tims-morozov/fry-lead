import os
import asyncio
import requests
import sqlite3
import html
from dotenv import load_dotenv
from telethon import TelegramClient, events

# 1. Загрузка конфигурации
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

TARGET_CHAT_NAMES = [
    'МИР КРЕАТОРОВ', 
    'Test Group Fry Lead',
    'Чат веб-дизайнеров | Фигма | Тильда | Разборы работ'
]

# --- База Данных ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

init_db()
client = TelegramClient('fry_lead_session', API_ID, API_HASH)

async def broadcast_order(text):
    """Рассылка заказа пользователям и логирование факта отправки"""
    users = get_all_users()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
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
    
    # Обобщенный лог без указания конкретных ID
    print(f"[SENT] Заказ успешно разослан пользователям (всего: {len(users)})")

async def process_message(event):
    try:
        sender_id = event.sender_id
        if not sender_id: return

        # Лог получения сообщения
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Чат')
        print(f"[RECEIVE] Получено новое сообщение из чата: {chat_title}")

        # Пытаемся получить никнейм
        username = None
        try:
            sender = await event.get_sender()
            if sender and hasattr(sender, 'username') and sender.username:
                username = sender.username
        except:
            pass

        # Формирование ссылки на сообщение
        message_id = event.id
        clean_chat_id = str(event.chat_id).replace("-100", "")
        msg_link = f"https://t.me/c/{clean_chat_id}/{message_id}"

        # Оформление строки клиента
        if username:
            user_link = f"https://t.me/{username}"
            client_display = f"<a href='{user_link}'>@{username}</a>"
        else:
            client_display = f"<a href='{msg_link}'>[Профиль скрыт — перейти к сообщению в чате]</a>"

        clean_text = html.escape(event.text or "")
        
        # Финальная верстка сообщения
        notification = (
            f"<b>🚀 НОВЫЙ ЗАКАЗ</b>\n\n"
            f"👤 <b>Клиент:</b> {client_display}\n"
            f"__________________________\n\n"
            f"{clean_text}"
        )
        
        await broadcast_order(notification)
        
    except Exception as e:
        print(f"[ERROR] Ошибка при обработке сообщения: {e}")

async def main():
    await client.start()
    print("[INFO] Скрипт запущен в боевом режиме. Ожидание заказов...")
    
    async def check_bot_updates():
        last_id = 0
        while True:
            try:
                res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_id + 1}").json()
                if res.get("ok"):
                    for upd in res["result"]:
                        last_id = upd["update_id"]
                        if "message" in upd and upd["message"].get("text") == "/start":
                            u_id = upd["message"]["from"]["id"]
                            add_user(u_id)
                            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                                          json={"chat_id": u_id, "text": "✅ Бот запущен! Ожидайте новые заказы."})
            except: pass
            await asyncio.sleep(5)

    asyncio.create_task(check_bot_updates())

    target_ids = []
    async for dialog in client.iter_dialogs():
        if dialog.name in TARGET_CHAT_NAMES:
            target_ids.append(dialog.id)
            print(f"[INFO] Мониторинг чата активен: {dialog.name}")

    @client.on(events.NewMessage(chats=target_ids))
    async def handler(event):
        await process_message(event)

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())