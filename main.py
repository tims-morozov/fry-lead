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
    "TARGET_CHATS": ["Timur Morozov", "Чат веб-дизайнеров | Фигма | Тильда | Разборы работ", "Работа IT", "МИР КРЕАТОРОВ"],
    "DAY_INTERVAL": (2.0, 4.0),
    "USER_DATA_DIR": "user_data",
    "SELECTORS": {
        "chat_button": ".ListItem-button",
        "unread_badge": ".tgKbsVmz, .chat-badge-transition span, .Badge.unread",
        "down_button": "button.Button.cxwA6gDO, .jump-down-button",
        "inner_unread": ".unviewed-count, .Badge.unread-count",
        "message_text": ".text-content, .message-text"
    }
}

async def log(msg): 
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def send_to_tg(chat_name, text):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
        users = cursor.fetchall()
        conn.close()
        for (user_id,) in users:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {"chat_id": user_id, "text": f"🚀 **НОВЫЙ ЗАКАЗ**\n📍 {chat_name}\n\n{text}", "parse_mode": "Markdown"}
            requests.post(url, json=payload, timeout=10)
    except Exception as e:
        await log(f"Ошибка связи: {e}")

async def get_messages(page, count):
    if count <= 0: return []
    return await page.evaluate(f"""(count) => {{
        const msgs = Array.from(document.querySelectorAll('.Message'));
        return msgs.slice(-count).map(m => {{
            const t = m.querySelector('.text-content, .message-text');
            return t ? t.innerText.trim() : null;
        }}).filter(x => x);
    }}""", count)

async def handle_unread_chat(page, chat_name):
    try:
        # Ищем чат с коротким таймаутом, чтобы не виснуть
        chats = page.locator(CONFIG["SELECTORS"]["chat_button"])
        target_chat = None
        
        chat_count = await chats.count()
        for i in range(chat_count):
            current = chats.nth(i)
            title_el = current.locator('.title, h3').first
            try:
                # Ждем текст заголовка не более 2 сек
                if await title_el.is_visible(timeout=2000):
                    title = (await title_el.inner_text()).strip()
                    if title == chat_name:
                        target_chat = current
                        break
            except: continue
        
        if not target_chat: return

        # Проверяем бадж (не более 3 сек ожидания)
        badge = target_chat.locator(CONFIG["SELECTORS"]["unread_badge"]).first
        try:
            if not await badge.is_visible(timeout=3000): return
            badge_text = await badge.inner_text()
            initial_count = int(''.join(filter(str.isdigit, badge_text)) or 1)
        except: return

        await log(f"[{chat_name}] Захожу (ожидаю {initial_count})...")
        await target_chat.click()
        await asyncio.sleep(1.5)

        # 1. Сбор основной пачки
        inner_badge = page.locator(CONFIG["SELECTORS"]["inner_unread"]).first
        real_count = initial_count
        if await inner_badge.is_visible(timeout=2000):
            real_count = int(''.join(filter(str.isdigit, await inner_badge.inner_text())) or initial_count)

        messages = await get_messages(page, real_count)
        for m in list(dict.fromkeys(messages)):
            await send_to_tg(chat_name, m)

        # 2. Быстрый спуск
        btn = page.locator(CONFIG["SELECTORS"]["down_button"]).first
        if await btn.is_visible(timeout=2000):
            await btn.click(force=True)
            await asyncio.sleep(0.5)

        await page.evaluate("""() => {
            const scrollable = document.querySelector('.MessageList.custom-scroll');
            if (scrollable) scrollable.scrollTop = scrollable.scrollHeight;
        }""")

        # 3. Оптимизированная охота
        for _ in range(3):
            await page.keyboard.press("End")
            await asyncio.sleep(0.8)
            
            # Если бадж исчез — выходим немедленно
            inner = page.locator(CONFIG["SELECTORS"]["inner_unread"]).first
            if not await inner.is_visible(timeout=1000):
                break
                
            # Если бадж все еще тут — добираем новые
            try:
                extra_text = await inner.inner_text()
                extra_count = int(''.join(filter(str.isdigit, extra_text)) or 0)
                if extra_count > 0:
                    await log(f"[{chat_name}] Добор: {extra_count}")
                    extra_msgs = await get_messages(page, extra_count)
                    for em in list(dict.fromkeys(extra_msgs)):
                        await send_to_tg(chat_name, em)
            except: break

        # Финальный выход
        await page.keyboard.press("End")
        await asyncio.sleep(1.0)
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.5)

    except Exception as e:
        await log(f"Ожидаемый пропуск в {chat_name}") # Ошибки таймаута теперь просто пропускают чат
        await page.keyboard.press("Escape")

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(CONFIG["USER_DATA_DIR"], headless=False)
        page = context.pages[0]
        await page.goto('https://web.telegram.org/a/')
        await log("Парзер запущен. Режим: Скорость + Точность.")
        await asyncio.sleep(15)
        while True:
            for chat in CONFIG["TARGET_CHATS"]:
                await handle_unread_chat(page, chat)
            await asyncio.sleep(random.uniform(*CONFIG["DAY_INTERVAL"]))

if __name__ == "__main__":
    asyncio.run(main())