import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID")) if os.getenv("API_ID") else None
API_HASH = os.getenv("API_HASH")

TARGET_CHAT_NAMES = [
    'МИР КРЕАТОРОВ', 
    'Test Group Fry Lead',
    'Чат веб-дизайнеров | Фигма | Тильда | Разборы работ',
    'Маркетологи Юга'
]

CATEGORIES = {
    # --- WEB DEVELOPMENT ---
    "NoCode": {
        "name": "Конструкторы сайтов (Tilda/WP)",
        "keywords": ["тильд", "tilda", "вордпресс", "wordpress", "wp", "лендинг", "многостраничник", "интернет-магазин"],
        "weight": 1.0
    },
    "Frontend": {
        "name": "Frontend-разработка",
        "keywords": ["верстк", "сверстать", "чистый код", "html", "css", "react", "vue", "разработка интерфейсов"],
        "weight": 1.1
    },
    "WebApps": {
        "name": "Web-Apps (SaaS)",
        "keywords": ["сложный сервис", "личный кабинет", "saas", "api интеграция", "интеграция по api"],
        "weight": 1.2
    },
    "MobileApps": {
        "name": "Mobile Apps",
        "keywords": ["мобильное приложение", "ios", "android", "flutter", "react native", "публикация в стор", "app store", "google play"],
        "weight": 1.3
    },

    # --- AUTOMATION & TECH ---
    "BusinessAutomation": {
        "name": "Business Automation",
        "keywords": ["интеграция crm", "amocrm", "bitrix24", "make.com", "integromat", "n8n", "yandex workflows", "связки"],
        "weight": 1.2
    },
    "SEO": {
        "name": "SEO",
        "keywords": ["seo", "сео", "аудит сайта", "оптимизация сайта", "продвижение сайта", "вывод в топ", "технический аудит"],
        "weight": 1.0
    },

    # --- DESIGN ---
    "WebDesign": {
        "name": "Web Design",
        "keywords": ["дизайн сайта", "отрисовать сайт", "дизайн лендинга"],
        "weight": 1.0
    },
    "UXUI": {
        "name": "UX/UI & Product Design",
        "keywords": ["ux/ui", "проектирование интерфейсов", "прототипирование", "figma", "фигма", "продуктовый дизайн"],
        "weight": 1.1
    },
    "GraphicDesign": {
        "name": "Graphic Design",
        "keywords": ["логотип", "иллюстрация", "фирменный стиль", "айдентика", "презентация", "упаковка", "брендбук"],
        "weight": 1.0
    },

    # --- AI & CONTENT ---
    "AIContent": {
        "name": "AI Content Generation",
        "keywords": ["генерация изображений", "midjourney", "stable diffusion", "генерация видео", "ai анимация", "ai 3d"],
        "weight": 1.2
    },
    "AIIntegration": {
        "name": "AI Integration",
        "keywords": ["внедрение ии", "автоответчик ии", "суммаризация", "llm", "ai ассистент"],
        "weight": 1.3
    },

    # --- TELEGRAM ECOSYSTEM ---
    "BotDev": {
        "name": "Bot Development",
        "keywords": ["разработка ботов", "тг-бот", "телеграм бот", "создать бота"],
        "weight": 1.0
    },
    "TWA": {
        "name": "Telegram Web Apps (TWA)",
        "keywords": ["twa", "web app telegram", "приложение внутри телеграм"],
        "weight": 1.4
    },
    "TelegramAutomation": {
        "name": "Automation Telegram",
        "keywords": ["парсер", "рассыльщик", "система мониторинга", "автоматизация телеграм"],
        "weight": 1.2
    },

    # --- MARKETING ---
    "SMM": {
        "name": "SMM & Content",
        "keywords": ["smm", "смм", "ведение канала", "контент", "стратегия", "упаковка смыслов"],
        "weight": 1.0
    },
    "LeadGen": {
        "name": "Lead Generation",
        "keywords": ["лидогенерация", "сбор лидов", "воронка продаж", "настройка воронок"],
        "weight": 1.1
    }
}

ORDER_MARKERS = [
    "кто может", "нужен", "ищу", "требуется", "задача", 
    "сделать", "разработать", "вакансия", "ищем в команду", 
    "сработаемся", "разрабатываем"
]

# ГЛОБАЛЬНЫЕ СТОП-СЛОВА (Добавлены фильтры для партнерских предложений)
GLOBAL_STOP_WORDS = [
    "помощник маркетолога", "бизнес-ассистент", "личный помощник", 
    "контроль подрядчиков", "обучаю", "предлагаю услуги", "мой опыт", 
    "продам", "подписка", "аккаунтов", "#помогу",
    "ведение календаря", "администрирование", "график 6/1", "сбор данных",
    "выплачиваем %", "за рекомендацию", "процент от заказа", "ищу партнеров"
]