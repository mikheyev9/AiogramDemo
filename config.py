import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    BASE_URL = os.getenv("BASE_URL")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))  # По умолчанию 6379 если не указано