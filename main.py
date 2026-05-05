import os
import asyncio
import requests
from dotenv import load_dotenv
from telethon import TelegramClient, events
from config import TARGET_CHAT_NAMES, CATEGORIES
from database import init_db, add_user
from utils import (
    broadcast_order, format_notification, classify_message, 
    get_categories_markup, toggle_user_category, get_user_categories
)

load_dotenv()
API_ID, API_HASH, BOT_TOKEN = int(os.getenv("API_ID")), os.getenv("API_HASH"), os.getenv("BOT_TOKEN")
init_db()
client = TelegramClient('fry_lead_session', API_ID, API_HASH)

async def process_message(event):
    try:
        if not event.text: return
        cat_id = classify_message(event.text)
        if not cat_id: return
        sender = await event.get_sender()
        username = getattr(sender, 'username', None)
        msg_link = f"https://t.me/c/{str(event.chat_id).replace('-100', '')}/{event.id}"
        await broadcast_order(format_notification(username, msg_link, event.text, cat_id), cat_id, BOT_TOKEN)
    except Exception as e: print(f"[ERROR Process] {e}")

async def check_bot_updates():
    last_id = 0
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_id + 1}&timeout=10").json()
            if not res.get("ok"): continue
            for upd in res["result"]:
                last_id = upd["update_id"]
                if "message" in upd and upd["message"].get("text") == "/start":
                    u_id = upd["message"]["from"]["id"]
                    add_user(u_id)
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                        "chat_id": u_id, 
                        "text": "Выберите категории, по которым хотите получать уведомления:", 
                        "reply_markup": get_categories_markup(u_id)
                    })
                elif "callback_query" in upd:
                    q = upd["callback_query"]
                    u_id, data = q["from"]["id"], q["data"]
                    
                    if data == "confirm_settings":
                        user_cats = get_user_categories(u_id)
                        all_cat_keys = list(CATEGORIES.keys())
                        
                        # Если выбраны все категории — пишем 'Все категории'[cite: 1]
                        if set(all_cat_keys).issubset(set(user_cats)):
                            display_cats = "Все категории"
                        else:
                            display_cats = ", ".join([CATEGORIES[c]['name'] for c in user_cats]) if user_cats else "Не выбрано"
                        
                        text = (
                            f"<b>Настройка завершена!</b>\n\n"
                            f"Выбранные категории: {display_cats}\n\n"
                            f"Теперь Вы будете получать только те заказы, которые соответствуют Вашему выбору."
                        )
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText", json={
                            "chat_id": u_id, 
                            "message_id": q["message"]["message_id"], 
                            "text": text, 
                            "parse_mode": "HTML"
                        })
                    else:
                        action = data.replace("toggle_", "") if data.startswith("toggle_") else data
                        new_markup = toggle_user_category(u_id, action)
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup", json={
                            "chat_id": u_id, 
                            "message_id": q["message"]["message_id"], 
                            "reply_markup": new_markup
                        })
        except Exception as e: print(f"[ERROR Bot] {e}")
        await asyncio.sleep(1)

async def main():
    await client.start()
    asyncio.create_task(check_bot_updates())
    target_ids = [d.id async for d in client.iter_dialogs() if d.name in TARGET_CHAT_NAMES]
    @client.on(events.NewMessage(chats=target_ids))
    async def handler(event): await process_message(event)
    print("--- БОТ ЗАПУЩЕН ---")
    await client.run_until_disconnected()

if __name__ == '__main__': asyncio.run(main())