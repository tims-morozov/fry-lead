import asyncio
import os
import random
import requests
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

CONFIG = {
    "TARGET_CHATS": ["Timur Morozov", "Заказы Фриланс", "Работа IT", "МИР КРЕАТОРОВ"],
    "DAY_INTERVAL": (2.0, 5.0),
    "USER_DATA_DIR": "user_data",
    "SELECTORS": {
        "chat_button": ".ListItem-button",
        "unread_badge": ".tgKbsVmz, .chat-badge-transition span, .Badge.unread",
        "messages": ".message-text, .text-content, .bubble-content"
    }
}

async def log(msg): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def send_to_telegram(chat_name, text):
    """Рассылает сообщение всем активным пользователям без фильтров"""
    try:
        if not os.path.exists('users.db'): return

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
        users = cursor.fetchall()
        conn.close()

        for (user_id,) in users:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": user_id,
                "text": f"🚀 **НОВЫЙ ЗАКАЗ**\n📍 Чат: {chat_name}\n\n{text}",
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload, timeout=5)
            
        if users:
            await log(f"Уведомление разослано пользователям ({len(users)} чел.)")
            
    except Exception as e:
        await log(f"Ошибка при рассылке: {e}")

async def handle_unread_chat(page, chat_name):
    try:
        # Поиск чата по точному имени
        chats = page.locator(CONFIG["SELECTORS"]["chat_button"])
        target_chat = None
        for i in range(await chats.count()):
            current = chats.nth(i)
            title_el = current.locator('.title, .peer-title, h3').first
            if await title_el.is_visible():
                title_text = await title_el.inner_text()
                if title_text.strip() == chat_name:
                    target_chat = current
                    break
        
        if not target_chat: return

        badge = target_chat.locator(CONFIG["SELECTORS"]["unread_badge"]).first
        if await badge.is_visible():
            badge_text = await badge.inner_text()
            count = int(''.join(filter(str.isdigit, badge_text)) or 1)
            
            await log(f"[{chat_name}] Найдено {count} новых. Читаю...")
            await target_chat.click()
            await asyncio.sleep(1.5)

            # Читаем сообщения
            await page.mouse.click(600, 400)
            await page.keyboard.press("End")
            await asyncio.sleep(0.5)

            messages = await page.evaluate(f"""(sel) => {{
                const msgs = Array.from(document.querySelectorAll(sel));
                return msgs.slice(-{count}).map(m => m.innerText.trim());
            }}""", CONFIG["SELECTORS"]["messages"])

            if messages:
                full_text = "\n".join([f"• {m.replace('\n', ' ')}" for m in messages if m])
                if full_text:
                    await send_to_telegram(chat_name, full_text)

            await asyncio.sleep(1)
            await page.keyboard.press("Escape")
            
    except Exception as e:
        await log(f"Ошибка в {chat_name}: {e}")
        await page.keyboard.press("Escape")

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            CONFIG["USER_DATA_DIR"], 
            headless=False,
            args=["--start-maximized"]
        )
        page = context.pages[0]
        await page.goto('https://web.telegram.org/a/')
        await log("Парзер запущен. Ожидание загрузки...")
        await asyncio.sleep(15)

        while True:
            for chat in CONFIG["TARGET_CHATS"]:
                await handle_unread_chat(page, chat)
            await asyncio.sleep(random.uniform(*CONFIG["DAY_INTERVAL"]))

if __name__ == "__main__":
    if not os.path.exists(CONFIG["USER_DATA_DIR"]): os.makedirs(CONFIG["USER_DATA_DIR"])
    asyncio.run(main())