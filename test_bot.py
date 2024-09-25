from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_API_KEY")
MAX_HISTORY = 5  

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['message_history'] = []
    await update.message.reply_text("Привет! Я бот, который помнит ваши сообщения. Напишите что-нибудь!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Я запоминаю ваши сообщения. Используйте /history, чтобы увидеть историю.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Добавляем новое сообщение в историю
    if 'message_history' not in context.user_data:
        context.user_data['message_history'] = []
    
    context.user_data['message_history'].append(update.message.text)
    
    # Ограничиваем историю последними MAX_HISTORY сообщениями
    context.user_data['message_history'] = context.user_data['message_history'][-MAX_HISTORY:]
    
    await update.message.reply_text(f"Я запомнил: {update.message.text}")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'message_history' not in context.user_data or not context.user_data['message_history']:
        await update.message.reply_text("У вас пока нет истории сообщений.")
    else:
        history_text = "\n".join(context.user_data['message_history'])
        await update.message.reply_text(f"Ваша история сообщений:\n{history_text}")

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Бот запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()