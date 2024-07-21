import os
from typing import Any, List
from dotenv import load_dotenv
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import OpenLLM
from yandex_chain import YandexLLM, YandexEmbeddings
from langchain.llms import GigaChat
from langchain_community.embeddings.gigachat import GigaChatEmbeddings
from langchain.vectorstores import Chroma  # Ensure this import is correct
from langchain.embeddings import HuggingFaceEmbeddings

class LLM:
    def __init__(self, llm_type: str = 'openai', **params):
        load_dotenv()
        llm_classes = {
            'openai': lambda: ChatOpenAI(api_key=os.environ.get('OPENAI_API_KEY'), **params),
            'open_source': lambda: OpenLLM(**params),
            'yandexgpt': lambda: YandexLLM(iam_token=os.environ.get('YC_IAM_TOKEN'), 
                                           folder_id=os.environ.get('YANDEX_FOLDER_ID'), **params),
            'gigachat': lambda: GigaChat(credentials=os.environ.get('GIGACHAT_CREDENTIALS'), 
                                         model='GigaChat:latest', verify_ssl_certs=False, 
                                         profanity_check=False, 
                                         ssl_verify=False, **params)
        }
        self.llm = llm_classes.get(llm_type, lambda: ValueError(f"Unsupported LLM type: {llm_type}"))()

class ChromaWrapper:
    def __init__(self, embedding_function: Any, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory

    def init_from_docs(self, docs: List[Document], collection_name='default'):
        self.langchain_chroma = Chroma.from_documents(
            docs, self.embedding_function,
            client=self.client,
            collection_name=collection_name,
        )

    def load(self):
        if os.path.exists(self.persist_directory):
            self.langchain_chroma = Chroma(
                client=self.client,
                embedding_function=self.embedding_function,
            )
        else:
            raise FileExistsError('Chroma is not initialized')

    def __getattr__(self, name):
        return getattr(self.langchain_chroma, name)

class RAG:
    def __init__(self, llm: LLM, retriever: Any, prompt: str = "rlm/rag-prompt"):
        self.prompt = hub.pull(prompt)
        self.rag_chain = (
            {"context": retriever | self._format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | llm.llm
            | StrOutputParser()
        )

    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def invoke(self, query):
        return self.rag_chain.invoke(query)

def main(olympiad_strings: List[str]):
    llm_type = 'gigachat'  # Change this to 'openai', 'yandexgpt', or 'gigachat' as needed
    params = {"temperature": 1, "max_tokens": 2000}

    embeddings = {
        'openai': OpenAIEmbeddings,
        'yandexgpt': lambda: YandexEmbeddings(iam_token=os.environ.get('YC_IAM_TOKEN'), folder_id=os.environ.get('YANDEX_FOLDER_ID')),
        'gigachat': lambda: HuggingFaceEmbeddings(model_name="sentence-transformers/LaBSE")
        
        # lambda: GigaChatEmbeddings(credentials=os.environ.get('GIGACHAT_CREDENTIALS'), 
        #                                        verify_ssl_certs=False,
        #                                        ssl_verify=False)
    }[llm_type]()

    llm = LLM(llm_type, **params)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # Convert olympiad strings to Documents
    docs = [Document(page_content=content) for content in olympiad_strings]

    # Split documents
    split_docs = splitter.split_documents(docs)

    # Initialize and populate Chroma DB
    vectorstore = ChromaWrapper(embedding_function=embeddings)
    vectorstore.init_from_docs(split_docs)

    rag_chain = RAG(llm, vectorstore.as_retriever())
    
    # # Example query
    # result = rag_chain.invoke("What are some upcoming olympiads?")
    # print(result)

if __name__ == "__main__":
    from parser_updated import main as parser_main
    olympiad_strings = parser_main()
    main(olympiad_strings)
