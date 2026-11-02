import os
from dotenv import load_dotenv

load_dotenv()

API_ID_RAW = os.getenv("API_ID", "").strip()
API_ID = int(API_ID_RAW) if API_ID_RAW.isdigit() else 0
API_HASH = os.getenv("API_HASH", "").strip()

SESSION_NAME = os.getenv("SESSION_NAME", "userbot_session").strip()
STRING_SESSION = os.getenv("STRING_SESSION", "").strip()

# Bot orqali bildirishnoma yuborish uchun (@BotFather bergan token)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID_RAW = os.getenv("OWNER_ID", "").strip()
OWNER_ID = int(OWNER_ID_RAW) if OWNER_ID_RAW.isdigit() else 0

DEFAULT_AUTO_REPLY = os.getenv(
    "AUTO_REPLY_TEXT",
    "Assalomu alaykum! Hozirda bandman yoki tarmoqda emasman. Bo'shashim bilan sizga albatta javob yozaman."
).strip()

REPLY_ONCE = os.getenv("REPLY_ONCE", "True").strip().lower() in ("true", "1", "yes")
NOTIFY_ME = os.getenv("NOTIFY_ME", "True").strip().lower() in ("true", "1", "yes")
CMD_PREFIX = os.getenv("CMD_PREFIX", ".").strip()
