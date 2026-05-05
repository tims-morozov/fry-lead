import sqlite3
from config import CATEGORIES

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            categories TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id):
    """При регистрации нового пользователя по умолчанию включаем все категории"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        all_cats = ",".join(CATEGORIES.keys())
        cursor.execute("INSERT INTO users (user_id, categories) VALUES (?, ?)", (user_id, all_cats))
        conn.commit()
    conn.close()