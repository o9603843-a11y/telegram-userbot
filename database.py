import sqlite3
import os
import time
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "userbot.db")


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Javob qaytarilgan foydalanuvchilar jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS replied_users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                last_replied_at TEXT,
                last_replied_timestamp REAL DEFAULT 0,
                reply_count INTEGER DEFAULT 1
            )
        """)

        # Agar ustun mavjud bo'lmasa qo'shish
        try:
            cursor.execute("ALTER TABLE replied_users ADD COLUMN last_replied_timestamp REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        # Bot sozlamalari jadvali
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()


def get_user_last_reply_time(user_id: int) -> float:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_replied_timestamp FROM replied_users WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        return float(res[0]) if (res and res[0] is not None) else 0.0


def has_user_been_replied(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM replied_users WHERE user_id = ? LIMIT 1", (user_id,))
        return cursor.fetchone() is not None


def record_reply_ts(user_id: int, first_name: str = "", username: str = "", timestamp: float = None):
    if timestamp is None:
        timestamp = time.time()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO replied_users (user_id, first_name, username, last_replied_at, last_replied_timestamp, reply_count)
            VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                last_replied_at = excluded.last_replied_at,
                last_replied_timestamp = excluded.last_replied_timestamp,
                reply_count = reply_count + 1,
                first_name = excluded.first_name,
                username = excluded.username
        """, (user_id, first_name, username, now_str, timestamp))
        conn.commit()


def reset_replies():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM replied_users")
        conn.commit()


def get_replied_count() -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM replied_users")
        res = cursor.fetchone()
        return res[0] if res else 0


def get_setting(key: str, default: str = None) -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
        res = cursor.fetchone()
        if res is not None:
            return res[0]
        return default


def set_setting(key: str, value: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bot_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))
        conn.commit()
