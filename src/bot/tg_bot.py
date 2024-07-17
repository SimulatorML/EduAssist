
import requests
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from telegram.ext.filters import TEXT
import threading

app = Flask(__name__)

# Хранилище данных
rag_system_url = "https://www.google.ru/"
api_key = "YOUR_API_KEY"

# Настройка Telegram бота
TELEGRAM_TOKEN = ''  # Токен вашего Telegram бота
bot = Bot(token=TELEGRAM_TOKEN)
application = Application.builder().token(TELEGRAM_TOKEN).build()


# Flask приложение для обработки запросов от RAG-системы
app = Flask(__name__)

@app.route('/')
def home():
    return "Flask сервер работает!"

# Приветственное сообщение и первичные инструкции
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Привет! Я ваш помощник. Пожалуйста, отправьте ваш запрос, и я передам его в систему для обработки."
    )
    await update.message.reply_text(welcome_message)

# Обработка сообщений от пользователя
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text  # Получаем текст сообщения от пользователя
    chat_id = update.message.chat_id  # Получаем ID чата пользователя

    try:
        # Отправка запроса в RAG-систему
        response = requests.post(
            rag_system_url,
            headers={'Authorization': f'Bearer {api_key}'},
            json={'query': user_message, 'chat_id': chat_id}
        )
        response.raise_for_status()  # Проверка успешности запроса

        # Обработка ответа от RAG-системы
        response_data = response.json()
        if 'answer' in response_data:
            await bot.send_message(chat_id=chat_id, text=f"Ответ от системы: {response_data['answer']}")
        else:
            await bot.send_message(chat_id=chat_id, text="Ошибка: не удалось получить ответ от системы.")
    except requests.exceptions.RequestException as e:
        # Обработка ошибок запроса
        await bot.send_message(chat_id=chat_id, text=f"Ошибка: не удалось связаться с системой. Причина: {e}")

# Маршрут для обработки запросов от RAG-системы
@app.route('/rag_response', methods=['POST'])
def rag_response():
    data = request.json  # Получаем данные из запроса
    chat_id = data.get('chat_id')  # Получаем ID чата
    response_text = data.get('response')  # Получаем текст ответа

    # Отправка ответа пользователю в Telegram
    if chat_id and response_text:
        bot.send_message(chat_id=chat_id, text=response_text)
        return jsonify({"status": "success"})
    return jsonify({"status": "failure"}), 400

# Настройка команд и обработчиков
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(TEXT & ~filters.COMMAND, handle_message))

# Запуск Flask-сервера в отдельном потоке
def run_flask():
    app.run(port=5000)

flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Запуск Telegram бота
application.run_polling()


# python "C:/Users/kowyn/OneDrive/Python_ds/Практика/RAG проект/main.py"
