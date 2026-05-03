import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/price_tracker")
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "default_token")
    NEMOCLAW_API_KEY = os.getenv("NEMOCLAW_API_KEY", "")

config = Config()
