from dotenv import load_dotenv
import os

load_dotenv()

FOLDER_ID = os.getenv('FOLDER_ID')
YANDEX_AIP_KEY = os.getenv('YANDEX_API_KEY')
print(FOLDER_ID, YANDEX_AIP_KEY)