import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

# --- НАСТРОЙКИ ---
TARGET_CHATS = ["Timur Morozov", "Заказы Фриланс", "Работа IT", "МИР КРЕАТОРОВ"]
CHECK_INTERVAL = 10 

async def check_telegram_connection(page):
    try:
        is_browser_online = await page.evaluate("window.navigator.onLine")
        if not is_browser_online: return False
        connecting_status = page.locator(".ConnectionStatus, .loading-indicator, .status-text")
        if await connecting_status.is_visible():
            status_text = await connecting_status.inner_text()
            if any(word in status_text.lower() for word in ["connecting", "updating", "соединение", "обновление"]):
                return False
        return True
    except: return False

async def handle_unread_chat(page, chat_name):
    try:
        chat_row = page.locator(".ListItem-button").filter(has_text=chat_name).first
        if not await chat_row.is_visible(): return False

        unread_badge = chat_row.locator(".tgKbsVmz, .chat-badge-transition span").first

        if await unread_badge.is_visible():
            badge_text = await unread_badge.inner_text()
            count = int(''.join(filter(str.isdigit, badge_text)) or 1)
            
            print(f"[*] [{datetime.now().strftime('%H:%M:%S')}] Чат '{chat_name}': {count} новых.")
            
            # 1. Заходим в чат
            await chat_row.click(force=True)
            await asyncio.sleep(1.5) 

            # --- УСИЛЕННЫЙ СКРОЛЛ (ФИКС) ---
            # Активируем окно чата
            await page.mouse.click(600, 400)
            
            # Нажимаем End трижды с микро-паузой (это заставляет движок TG прогрузить хвост)
            for _ in range(3):
                await page.keyboard.press("End")
                await asyncio.sleep(0.2)

            # Проверяем ту самую кнопку из твоего инспектора
            # Добавил еще один вариант селектора .was-unread .Button
            scroll_btn = page.locator("button.Button.round[aria-label='Go to bottom'], .scroll-down-button").filter(visible=True).first
            if await scroll_btn.is_visible():
                await scroll_btn.click(force=True)
                print(f"   [v] Нажата кнопка 'Вниз'")
            
            # "Прокрутка колесиком" до упора через JS
            await page.evaluate("""
                const scrollable = document.querySelector('.MessageList, .messages-container, .Transition_slide-active .scrollable-alist');
                if (scrollable) {
                    scrollable.scrollTo({ top: scrollable.scrollHeight, behavior: 'smooth' });
                }
            """)
            
            # Критически важная пауза, чтобы "галочки" стали синими
            await asyncio.sleep(2) 
            # -------------------------------

            # 4. Собираем сообщения
            msg_selectors = ".message-text, .text-content, .bubble-content"
            messages = await page.query_selector_all(msg_selectors)
            
            if messages:
                new_ones = messages[-count:]
                print(f"\n>>> НОВЫЕ СООБЩЕНИЯ В '{chat_name}':")
                for m in new_ones:
                    text = (await m.inner_text()).strip()
                    print(f"  > {text}")
                print("-" * 40)
            
            # 5. Выходим через Escape
            await page.keyboard.press("Escape")
            await asyncio.sleep(1) 
            return True
    except Exception: pass
    return False

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            'user_data', 
            headless=False,
            slow_mo=50
        )
        page = await context.new_page()
        await page.goto('https://web.telegram.org/a/')

        print("Загрузка (20 сек)...")
        await asyncio.sleep(20)
        
        print("--- МОНИТОРИНГ ЗАПУЩЕН ---")

        while True:
            if not await check_telegram_connection(page):
                await asyncio.sleep(5)
                continue

            for chat in TARGET_CHATS:
                await handle_unread_chat(page, chat)
            
            try:
                await page.mouse.move(150, 400)
                await page.mouse.wheel(0, 500)
                await asyncio.sleep(1)
                await page.mouse.wheel(0, -500)
            except: pass

            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\nОстановлено.")