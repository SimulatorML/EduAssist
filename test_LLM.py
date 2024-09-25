import os
from dotenv import load_dotenv
from app.LLM import YandexLLM

load_dotenv()

FOLDER_ID = os.getenv('FOLDER_ID')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')

messages = [
        {
            "role": "system",
            "text": "Ты ассистент дроид, способный помочь в галактических приключениях."
        },
        {
            "role": "user",
            "text": "Привет, Дроид! Мне нужна твоя помощь, чтобы узнать больше о Силе. Как я могу научиться ее использовать?"
        },
        {
            "role": "assistant",
            "text": "Привет! Чтобы овладеть Силой, тебе нужно понять ее природу. Сила находится вокруг нас и соединяет всю галактику. Начнем с основ медитации."
        },
    ]

message = "Хорошо, а как насчет строения светового меча? Это важная часть тренировки джедая. Как мне создать его?"

llm = YandexLLM(FOLDER_ID, YANDEX_API_KEY,)

print(llm.answer(messages, message))