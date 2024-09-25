import os

from dotenv import load_dotenv
from app.LLM import YandexGPT

load_dotenv()


folder_id = os.getenv("FOLDER_ID")
Yandex_api_key = os.getenv("YANDEX_API_KEY")