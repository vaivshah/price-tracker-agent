import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/price_tracker")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "default_token")
    NEMOCLAW_API_KEY = os.getenv("NEMOCLAW_API_KEY", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/push")
    OPENCLAW_URL = os.getenv("OPENCLAW_URL", "http://openclaw:18789")
    OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

config = Config()
