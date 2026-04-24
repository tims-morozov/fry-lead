import asyncio
import os
import random
import requests
from datetime import datetime
from playwright.async_api import async_playwright

# --- НАСТРОЙКИ ТЕЛЕГРАМ-БОТА ---
BOT_TOKEN = "ТВОЙ_ТОКЕН_ОТ_BOTFATHER"
MY_CHAT_ID = "ТВОЙ_CHAT_ID"

# --- КОНФИГУРАЦИЯ ---
CONFIG = {
    "TARGET_CHATS": ["Timur Morozov", "Заказы Фриланс", "Работа IT", "МИР КРЕАТОРОВ"],
    "DAY_INTERVAL": (1.5, 3.5),
    "NIGHT_INTERVAL": (900, 1200),
    "WORK_HOURS": (8, 0), # С 8 утра до 00:00 активный режим
    "USER_DATA_DIR": "user_data",
    "SELECTORS": {
        "chat_button": ".ListItem-button",
        "unread_badge": ".tgKbsVmz, .chat-badge-transition span, .Badge.unread",
        "messages": ".message-text, .text-content, .bubble-content"
    }
}

async def send_to_telegram(chat_name, text):
    """Отправляет уведомление в твой личный чат"""
    try:
        # Экранируем Markdown или используем простой текст
        message = f"🔔 **НОВЫЙ ЗАКАЗ**\n📍 Чат: {chat_name}\n\n{text}"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": MY_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[!] Ошибка отправки уведомления: {e}")

async def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def is_work_time():
    now = datetime.now().hour
    start, end = CONFIG["WORK_HOURS"]
    if start < end:
        return start <= now < end
    else:
        return now >= start or now < end

async def human_sleep(min_s, max_s):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def handle_unread_chat(page, chat_name):
    try:
        chat_locator = page.locator(CONFIG["SELECTORS"]["chat_button"]).filter(has_text=chat_name).first
        if not await chat_locator.is_visible(): return

        badge = chat_locator.locator(CONFIG["SELECTORS"]["unread_badge"]).first
        if await badge.is_visible():
            badge_text = await badge.inner_text()
            count = int(''.join(filter(str.isdigit, badge_text)) or 1)
            
            await log(f"[{chat_name}] Вижу {count}. Читаю...")
            await chat_locator.click(force=True, timeout=3000)
            await asyncio.sleep(1.2) 

            # --- СИЛОВОЕ ПРОЧТЕНИЕ (для длинных сообщений) ---
            # Кликаем в центр области сообщений для фокуса
            await page.mouse.click(600, 400)
            
            # Прокрутка через JS и горячие клавиши
            await page.evaluate("""
                const el = document.querySelector('.MessageList, .messages-container, .scrollable-alist');
                if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'auto' });
            """)
            await page.keyboard.press("End")
            await asyncio.sleep(0.5)
            await page.keyboard.press("PageDown") 

            # Сбор текста через JS (строго последние 'count')
            messages_text = await page.evaluate(f"""(selector) => {{
                const msgs = Array.from(document.querySelectorAll(selector));
                return msgs.slice(-{count}).map(m => m.innerText.trim());
            }}""", CONFIG["SELECTORS"]["messages"])

            if messages_text:
                full_alert_text = ""
                print(f"\n>>> {chat_name.upper()}:")
                for t in messages_text:
                    if t:
                        clean_t = t.replace('\n', ' ')
                        print(f"  > {clean_t}")
                        full_alert_text += f"• {clean_t}\n"
                
                if full_alert_text:
                    await send_to_telegram(chat_name, full_alert_text)

            # КРИТИЧНО: Ждем, чтобы Telegram успел пометить чат прочитанным
            await asyncio.sleep(1.5)
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.8) 
            
    except Exception:
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
        await log("Система запущена. Ждем загрузки...")
        await asyncio.sleep(15)

        while True:
            try:
                if is_work_time():
                    for chat in CONFIG["TARGET_CHATS"]:
                        await handle_unread_chat(page, chat)
                    await human_sleep(*CONFIG["DAY_INTERVAL"])
                else:
                    await log("Ночной режим: сон...")
                    await human_sleep(*CONFIG["NIGHT_INTERVAL"])
                    for chat in CONFIG["TARGET_CHATS"]:
                        await handle_unread_chat(page, chat)
            except Exception as e:
                await log(f"Ошибка в основном цикле: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    if not os.path.exists(CONFIG["USER_DATA_DIR"]): os.makedirs(CONFIG["USER_DATA_DIR"])
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")