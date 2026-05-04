import os
import asyncio
import requests
from dotenv import load_dotenv
from telethon import TelegramClient, events
from config import TARGET_CHAT_NAMES
from database import init_db, add_user
from utils import broadcast_order, format_notification

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

init_db()
client = TelegramClient('fry_lead_session', API_ID, API_HASH)

async def process_message(event):
    try:
        sender_id = event.sender_id
        if not sender_id: return

        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', 'Чат')
        print(f"[RECEIVE] Получено новое сообщение из чата: {chat_title}")

        username = None
        try:
            sender = await event.get_sender()
            if sender and hasattr(sender, 'username') and sender.username:
                username = sender.username
        except:
            pass

        message_id = event.id
        clean_chat_id = str(event.chat_id).replace("-100", "")
        msg_link = f"https://t.me/c/{clean_chat_id}/{message_id}"

        notification = format_notification(username, msg_link, event.text)
        await broadcast_order(notification, BOT_TOKEN)
        
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
                                          json={"chat_id": u_id, "text": "✅ Бот запущен!"})
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