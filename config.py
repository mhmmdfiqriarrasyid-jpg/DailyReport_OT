import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Jayapura")
DATABASE_PATH = os.getenv("DATABASE_PATH", "reports.db")
OUTPUT_DIR = "outputs"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN belum diset di file .env")
if not ALLOWED_USER_ID:
    raise ValueError("ALLOWED_USER_ID belum diset di file .env")
