import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

# --- КОНФИГУРАЦИЯ ---
CONFIG = {
    "TARGET_CHATS": ["Timur Morozov", "Заказы Фриланс", "Работа IT", "МИР КРЕАТОРОВ"],
    "CHECK_INTERVAL": 5,  # Уменьшили интервал для более быстрой реакции
    "USER_DATA_DIR": "user_data",
    "SELECTORS": {
        "chat_button": ".ListItem-button",
        "unread_badge": ".tgKbsVmz, .chat-badge-transition span, .Badge.unread",
        "scroll_btn": "button[aria-label='Go to bottom'], button[title='Go to bottom'], .scroll-down-button",
        "messages": ".message-text, .text-content, .bubble-content",
        "unread_sep": ".message-list-item:has-text('Unread Messages'), .message-list-item:has-text('Новые сообщения')"
    }
}

async def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

async def safe_scroll_to_bottom(page):
    """Улучшенный скролл вниз без лишних движений"""
    # Активируем окно кликом в безопасную зону (заголовок)
    await page.mouse.click(600, 50)
    
    # Силовой проброс вниз через клавиши
    for _ in range(2):
        await page.keyboard.press("End")
        await asyncio.sleep(0.3)
    
    # Проверка и нажатие кнопки "Вниз"
    btn = page.locator(CONFIG["SELECTORS"]["scroll_btn"]).filter(visible=True).first
    if await btn.is_visible():
        await btn.click(force=True)
    
    # Финальный JS-скролл для подгрузки всех элементов
    await page.evaluate("""
        const el = document.querySelector('.MessageList, .messages-container, .Transition_slide-active .scrollable-alist');
        if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'auto' });
    """)

async def handle_unread_chat(page, chat_name):
    try:
        chat_locator = page.locator(CONFIG["SELECTORS"]["chat_button"]).filter(has_text=chat_name).first
        if not await chat_locator.is_visible():
            return

        badge = chat_locator.locator(CONFIG["SELECTORS"]["unread_badge"]).first
        if await badge.is_visible():
            badge_text = await badge.inner_text()
            count = int(''.join(filter(str.isdigit, badge_text)) or 1)
            
            await log(f"Чат '{chat_name}': {count} новых. Захожу...")
            await chat_locator.click(force=True)
            await asyncio.sleep(1) # Время на анимацию открытия

            await safe_scroll_to_bottom(page)
            await asyncio.sleep(1.5) # Ждем, пока сообщения "прочитаются"

            # Сбор сообщений через разделитель
            separator = page.locator(CONFIG["SELECTORS"]["unread_sep"]).last
            msgs_locator = page.locator(CONFIG["SELECTORS"]["messages"])
            
            if await separator.is_visible():
                # Берем всё, что ниже плашки "Новые сообщения"
                new_msgs = page.locator(f".message-list-item:below({CONFIG['SELECTORS']['unread_sep']}) {CONFIG['SELECTORS']['messages']}")
                texts = await new_msgs.all_inner_texts()
            else:
                # Фоллбэк: берем последние N сообщений по счетчику
                all_texts = await msgs_locator.all_inner_texts()
                texts = all_texts[-count:] if all_texts else []

            if texts:
                print(f"\n>>> {chat_name.upper()}:")
                for t in texts:
                    print(f"  > {t.strip()[:200]}...") # Ограничили длину для чистоты консоли
                print("-" * 30)

            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            
    except Exception:
        pass

async def main():
    async with async_playwright() as p:
        # Оптимизация: отключаем картинки для экономии трафика и скорости
        context = await p.chromium.launch_persistent_context(
            CONFIG["USER_DATA_DIR"],
            headless=False,
            args=["--start-maximized", "--blink-settings=imagesEnabled=false"] 
        )
        
        page = context.pages[0]
        await page.goto('https://web.telegram.org/a/')
        await log("Ожидание загрузки (15 сек)...")
        await asyncio.sleep(15)

        while True:
            # Вместо простого цикла, проверяем только когда есть активность
            for chat in CONFIG["TARGET_CHATS"]:
                await handle_unread_chat(page, chat)
            
            await asyncio.sleep(CONFIG["CHECK_INTERVAL"])

if __name__ == "__main__":
    if not os.path.exists(CONFIG["USER_DATA_DIR"]):
        os.makedirs(CONFIG["USER_DATA_DIR"])
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановлено.")