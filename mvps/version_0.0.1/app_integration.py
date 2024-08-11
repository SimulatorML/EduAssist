import os
from dotenv import load_dotenv
from rag_updated import RAG, LLM, ChromaWrapper
from tg_bot_simplified import TelegramBot
from parser_updated import main as parser_main
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from yandex_chain import YandexLLM, YandexEmbeddings
from langchain_community.embeddings.gigachat import GigaChatEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def initialize_rag():
    load_dotenv()
    
    llm_type = 'gigachat'  # Change this as needed
    params = {"temperature": 0.7, "max_tokens": 2000}

    embeddings = {
        'openai': OpenAIEmbeddings,
        'yandexgpt': lambda: YandexEmbeddings(iam_token=os.environ['YC_IAM_TOKEN'], folder_id=os.environ['YANDEX_FOLDER_ID']),
        'gigachat': lambda: HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
        # lambda: GigaChatEmbeddings(credentials=os.environ['GIGACHAT_CREDENTIALS'],
        #                                        verify_ssl_certs=False,
        #                                        ssl_verify=False)
    }[llm_type]()

    llm = LLM(llm_type, **params)

    # Initialize and populate Chroma DB
    vectorstore = ChromaWrapper(embedding_function=embeddings)
    
    # Check if the database already exists
    try:
        vectorstore.load()
        print("Loaded existing Chroma database.")
    except FileExistsError:
        print("Initializing new Chroma database...")
        olympiad_strings = parser_main()
        docs = [Document(page_content=content) for content in olympiad_strings]
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = splitter.split_documents(docs)
        vectorstore.init_from_docs(split_docs)
        print("Chroma database initialized with parsed data.")

    return RAG(llm, vectorstore.as_retriever())

def main():
    rag_system = initialize_rag()
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    
    if not telegram_token:
        raise ValueError("TELEGRAM_TOKEN not found in environment variables.")
    
    bot = TelegramBot(telegram_token, rag_system)
    print("Starting Telegram bot...")
    bot.run()

if __name__ == "__main__":
    main()
