import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from LLM import llm_type
from chroma_db_managment import ChromaManager

load_dotenv()
TOKEN = os.getenv("TELEGRAM_API_KEY")
MAX_HISTORY = 10

model = llm_type()

manager = ChromaManager()
manager.load("raw_data")

dump_storage = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['message_history'] = []
    await update.message.reply_text("Привет! Я бот, который может ответить на вопросы об олимпиадах. Что вы хотите узнать?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я бот, который может ответить на вопросы об олимпиадах. Что вы хотите узнать?")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Добавляем новое сообщение в историю
    user_id = update.message.from_user.id
    if user_id not in dump_storage:
        dump_storage[user_id] = [{   
                "role": "system",
                "text": "Привет, ты мой собеседник, который рассказывает мне обо всех своих возможностях!"
        }]

    messages = dump_storage[user_id]
        

    user_message = update.message.text

    nearest = manager.find_most_similar(user_message)

    answer = model.answer(messages, user_message, nearest[0])

    user_m = {
        "role": "user",
        "text": user_message,
    }
    assistant_m = {
        "role": "assistant",
        "text": answer["text"]
    }
    
    # Ограничиваем историю последними MAX_HISTORY сообщениями
    messages += [user_m, assistant_m]
    if len(messages) > 10:
        messages = messages[:1] + messages[-9:]

    dump_storage[user_id] = messages
    
    await update.message.reply_text(f"{answer['text']}")

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()