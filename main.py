import asyncio
import os
import random
from datetime import datetime
from playwright.async_api import async_playwright

# --- КОНФИГУРАЦИЯ ---
CONFIG = {
    "TARGET_CHATS": ["Timur Morozov", "Заказы Фриланс", "Работа IT", "МИР КРЕАТОРОВ"],
    "DAY_INTERVAL": (1.5, 3.5),    # Днем — скорость хищника
    "NIGHT_INTERVAL": (900, 1200), # Ночью — проверка раз в 15-20 минут
    "WORK_HOURS": (8, 0),          # С 8 утра до 00:00 — активный режим
    "USER_DATA_DIR": "user_data",
    "SELECTORS": {
        "chat_button": ".ListItem-button",
        "unread_badge": ".tgKbsVmz, .chat-badge-transition span, .Badge.unread",
        "messages": ".message-text, .text-content, .bubble-content"
    }
}

async def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def is_work_time():
    """Проверяет, попадает ли текущее время в рабочий диапазон"""
    now = datetime.now().hour
    start, end = CONFIG["WORK_HOURS"]
    if start < end:
        return start <= now < end
    else: # Если диапазон переходит через полночь (как у нас: 8:00 - 00:00)
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
            
            await log(f"[{chat_name}] Найдено {count}. Читаю...")
            await chat_locator.click(force=True, timeout=3000)
            await asyncio.sleep(1.0) 

            # Скролл и чтение
            await page.keyboard.press("End")
            await asyncio.sleep(0.5)

            messages_text = await page.evaluate(f"""(selector) => {{
                const msgs = Array.from(document.querySelectorAll(selector));
                return msgs.slice(-{count}).map(m => m.innerText.trim());
            }}""", CONFIG["SELECTORS"]["messages"])

            if messages_text:
                print(f"\n>>> {chat_name.upper()}:")
                for t in messages_text:
                    if t: print(f"  > {t.replace('\n', ' ')}")
                print("-" * 35)

            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
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
        await log("Система запущена. Ожидание загрузки интерфейса...")
        await asyncio.sleep(15)

        while True:
            try:
                # Определяем текущий режим
                if is_work_time():
                    # АКТИВНЫЙ ДЕНЬ
                    for chat in CONFIG["TARGET_CHATS"]:
                        await handle_unread_chat(page, chat)
                    await human_sleep(*CONFIG["DAY_INTERVAL"])
                else:
                    # ТИХАЯ НОЧЬ
                    await log("Ночной режим: засыпаю...")
                    await human_sleep(*CONFIG["NIGHT_INTERVAL"])
                    # Ночью проверяем чаты только один раз после долгого сна
                    for chat in CONFIG["TARGET_CHATS"]:
                        await handle_unread_chat(page, chat)
                
            except Exception as e:
                await log(f"Ошибка цикла: {e}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    if not os.path.exists(CONFIG["USER_DATA_DIR"]): os.makedirs(CONFIG["USER_DATA_DIR"])
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма остановлена.")