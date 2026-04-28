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
        "chat_list_container": ".Transition_slide-active .MessageList"
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

async def handle_unread_chat(page, chat_name):
    try:
        chats = page.locator(CONFIG["SELECTORS"]["chat_button"])
        target_chat = None
        for i in range(await chats.count()):
            current = chats.nth(i)
            title_el = current.locator('.title, h3').first
            if await title_el.is_visible() and (await title_el.inner_text()).strip() == chat_name:
                target_chat = current
                break
        
        if not target_chat: return
        badge = target_chat.locator(CONFIG["SELECTORS"]["unread_badge"]).first
        
        if await badge.is_visible():
            count = int(''.join(filter(str.isdigit, await badge.inner_text())) or 1)
            await log(f"[{chat_name}] Вижу {count}. Читаю...")
            await target_chat.click()
            await asyncio.sleep(2)

            # 1. Сбор сообщений
            messages = await page.evaluate(f"""(count) => {{
                const msgs = Array.from(document.querySelectorAll('.Message'));
                return msgs.slice(-count).map(m => {{
                    const t = m.querySelector('.text-content, .message-text');
                    return t ? t.innerText.trim() : null;
                }}).filter(x => x);
            }}""", count)
            
            for m in list(dict.fromkeys(messages)):
                await send_to_tg(chat_name, m)

            # 2. СИЛОВОЕ ПРОЧТЕНИЕ
            # Прожимаем кнопку вниз
            for _ in range(8):
                btn = page.locator(CONFIG["SELECTORS"]["down_button"]).first
                if await btn.is_visible():
                    await btn.click(force=True)
                    await asyncio.sleep(0.4)
                else: break

            # Скроллим сам контейнер сообщений в самый низ через JS
            await page.evaluate("""() => {
                const scrollable = document.querySelector('.MessageList.custom-scroll');
                if (scrollable) scrollable.scrollTop = scrollable.scrollHeight;
            }""")
            
            # Ждем исчезновения внутреннего баджа
            read_confirmed = False
            for _ in range(5):
                await page.keyboard.press("End")
                await asyncio.sleep(1.0)
                inner = page.locator(CONFIG["SELECTORS"]["inner_unread"]).first
                if not await inner.is_visible():
                    read_confirmed = True
                    break
            
            # 3. ЕСЛИ ВСЕ ЕЩЕ НЕ ПРОЧИТАНО — МЕНЮ
            if not read_confirmed:
                await log(f"[{chat_name}] Обычный скролл не помог. Жму 'Mark as Read'...")
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                await target_chat.click(button="right")
                # Ищем пункт меню "Mark as read"
                menu_item = page.locator(".context-menu-item:has-text('Mark as read'), .tgico-readall").first
                if await menu_item.is_visible():
                    await menu_item.click()
            else:
                await page.keyboard.press("Escape")
            
            await asyncio.sleep(1)

    except Exception as e:
        await log(f"Ошибка: {e}")
        await page.keyboard.press("Escape")

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(CONFIG["USER_DATA_DIR"], headless=False)
        page = context.pages[0]
        await page.goto('https://web.telegram.org/a/')
        await log("Система запущена. Режим: Гарантированное прочтение.")
        await asyncio.sleep(15)
        while True:
            for chat in CONFIG["TARGET_CHATS"]:
                await handle_unread_chat(page, chat)
            await asyncio.sleep(random.uniform(*CONFIG["DAY_INTERVAL"]))

if __name__ == "__main__":
    asyncio.run(main())