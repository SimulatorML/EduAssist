import os

from typing import Any

import bs4

from dotenv import load_dotenv

from langchain import hub

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents.base import Document as LangChainDocument
from langchain_core.vectorstores.base import VectorStoreRetriever

#web loader
from langchain_community.document_loaders import WebBaseLoader

# chankers
from langchain_text_splitters import RecursiveCharacterTextSplitter

# vector dd
import chromadb
from chromadb.config import Settings

from langchain_chroma import Chroma

# LLMs and embeddings
from langchain_community.llms import OpenLLM

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

from yandex_chain import YandexLLM, YandexEmbeddings


class LLM:
    """Wrapper on LLM models. Three possible vriants are availible: 'openai', 'open_source', 'yandexgpt'.
    
    Args: 
          llm_type: str : LLM provider name
          model: str : model mane, opt.
          server_url: str : model server url, opt.
          params: dict : model parameters, depend on provider
    """
    def __init__(self, llm_type: str ='openai', model: str = None, server_url:str = None, **params):
        load_dotenv()
        if llm_type=='openai':
            try:
                self.llm = ChatOpenAI(model=model, api_key=os.environ['OPENAI_API_KEY'])
            except:
                self.llm = ChatOpenAI(model="gpt-3.5-turbo-0125", 
                                      api_key=os.environ['OPENAI_API_KEY'], 
                                      **params)
        elif llm_type=='open_source':
            try:
                self.llm = OpenLLM(server_url=server_url, **params)
            except:
                raise ValueError('Check if server_url is correct!')
        elif llm_type=='yandexgpt':
            self.llm = YandexLLM(iam_token=os.environ['YC_IAM_TOKEN'], 
                                 folder_id=os.environ['YANDEX_FOLDER_ID'],
                                 **params)


class Splitter:
    """Wrapper on langchain_text_splitters module.
    """
    def __init__(self, method: str, methods: dict, **params):
        self.splitter = methods[method](**params)
    
    def __getattr__(self, name):
        return getattr(self.splitter, name)


class ChromaWrapper:
    """Wrapper for Chroma. 
    Allows initializing the db from documents and loading previously initialized db.
    
    Args:
        embedding_function: emdedder 
        persist_directory: path to bd
    """
    def __init__(self, embedding_function: Any, persist_directory: str ="./chroma_db"):
        load_dotenv()
        
        self.persistent_client = chromadb.PersistentClient(path=persist_directory,
                                                          settings=Settings(allow_reset=True))
        self.embedding_function = embedding_function
        self.persist_directory = persist_directory

    def init_from_docs(self, docs: list[LangChainDocument], collection_name='default'):
        """Initialise db from documents.
        Args: 
          List(langchain_core.documents.base.Document) : list of langchain docs
          collection_name: str : collection name
        """
        self.persistent_client.reset()
        self.langchain_chroma = Chroma.from_documents(
                                docs, self.embedding_function,
                                client=self.persistent_client,
                                collection_name=collection_name,
                            )
        self.collection_name = collection_name
    
    def load(self):
        """Loads db
        """
        if os.path.exists(self.persist_directory):
            self.langchain_chroma = Chroma(
                                    client=self.persistent_client,
                                    embedding_function=self.embedding_function,
                                )
        else:
            raise FileExistsError('Chroma is not initialized')

    def __getattr__(self, name):
        return getattr(self.langchain_chroma, name)

  
class RAG:
    """Warper on langchain RAG
    """

    def __init__(self, llm: LLM, retriever: VectorStoreRetriever,
                 prompt: str = "rlm/rag-prompt",
                ):

        self.prompt = hub.pull(prompt)
        
        self.rag_chain = (
                    {"context": retriever | _format_docs, "question": RunnablePassthrough()}
                    | self.prompt
                    | llm
                    | StrOutputParser()
                )

    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def invoke(self, query):
        return self.rag_chain.invoke(query)


if __name__ == "__main__":

    # llm and embeddings provider selection
    llm_type = 'openai'

    if llm_type == 'yandexgpt':
        embeddings = YandexEmbeddings(iam_token=os.environ['YC_IAM_TOKEN'], 
                                      folder_id=os.environ['YANDEX_FOLDER_ID'])

        params = {
            "model_uri": f'gpt://{os.getenv("YANDEX_FOLDER_ID")}/yandexgpt/latest',
            "temperature": 1,
            "max_tokens": 2000,
        }
        llm = LLM(llm_type='yandexgpt', **params).llm

    elif llm_type == 'openai':
        embeddings = OpenAIEmbeddings()

        params = {
            "temperature": 1,
            "max_tokens": 2000,
        }

        llm = LLM(llm_type=llm_type, **params).llm
    else:
        ...

    # web parsing plug

    loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs=dict(
        parse_only=bs4.SoupStrainer(
            class_=("post-content", "post-title", "post-header")
        )
    ),
    )
    docs = loader.load()

    # splitter
    methods = {'RecursiveCharacterTextSplitter': RecursiveCharacterTextSplitter}
    params = {'chunk_size': 1000, 
              'chunk_overlap': 200}
    splitter = Splitter('RecursiveCharacterTextSplitter', methods, **params)

    vectorstore = ChromaWrapper(embedding_function=embeddings)
    vectorstore.init_from_docs(splitter.split_documents(docs))


    rag_chain = RAG(llm, vectorstore.as_retriever())

    rag_chain.invoke("What is Task Decomposition?")
