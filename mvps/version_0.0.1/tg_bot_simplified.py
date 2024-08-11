import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

class TelegramBot:
    def __init__(self, token, rag_system):
        self.application = Application.builder().token(token).build()
        self.rag_system = rag_system

        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, _):
        await update.message.reply_text("Привет! Я бот, который может ответить на вопросы об олимпиадах. Что вы хотите узнать?")

    async def handle_message(self, update: Update, _):
        user_message = update.message.text
        response = self.rag_system.invoke(user_message)
        await update.message.reply_text(response)

    def run(self):
        self.application.run_polling()

if __name__ == "__main__":
    # This part is for testing the bot independently
    from dotenv import load_dotenv
    load_dotenv()
    
    # Mock RAG system for testing
    class MockRAG:
        def invoke(self, query):
            return f"Mocked response to: {query}"

    bot = TelegramBot(os.getenv('TELEGRAM_TOKEN'), MockRAG())
    bot.run()
