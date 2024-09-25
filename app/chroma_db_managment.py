import chromadb
import requests
import os
from dotenv import load_dotenv
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List
from time import sleep

load_dotenv()

FOLDER_ID = os.getenv('FOLDER_ID')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')

doc_uri = f"emb://{FOLDER_ID}/text-search-doc/latest"
query_uri = f"emb://{FOLDER_ID}/text-search-query/latest"

embed_url = "https://llm.api.cloud.yandex.net:443/foundationModels/v1/textEmbedding"
headers = {"Content-Type": "application/json", "Authorization": f"Api-Key {YANDEX_API_KEY}", "x-folder-id": f"{FOLDER_ID}"}

def get_yandex_gpt_embeddings(text: str, text_type: str = "doc") -> List[float]:
    query_data = {
        "modelUri": doc_uri if text_type == "doc" else query_uri,
        "text": text,
    }

    response = requests.post(embed_url, json=query_data, headers=headers)
    sleep(0.13)

    if response.status_code == 200:
        return response.json().get("embedding")

    raise Exception(f"Failed to get embeddings: {response.status_code}, {response.text}")

class YandexGPTEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __call__(self, texts: List[str]) -> List[List[float]]:
        return [get_yandex_gpt_embeddings(text, "doc") for text in texts]


class ChromaManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.embedding_function = YandexGPTEmbeddingFunction()
        self.collection = None

    def create_collection(self, strings: List[str], collection_name: str):
        self.collection = self.client.create_collection(
            name=collection_name, 
            embedding_function=self.embedding_function
        )

        ids = [f"id_{i}" for i in range(len(strings))]
        metadatas = [{"source": f"string_{i}"} for i in range(len(strings))]

        self.collection.add(
            documents=strings,
            metadatas=metadatas,
            ids=ids
        )

    def load(self, collection_name: str='default'):
        collection_names = [c.name for c in self.client.list_collections()]

        if collection_name in collection_names:
            self.collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=self.embedding_function
            )
        else:
            raise FileNotFoundError('Collection not found')

    def find_most_similar(self, query: str, k: int = 1) -> List[str]:
        if self.collection is None:
            raise ValueError("No collection loaded. Call load() or create_collection() first.")

        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )

        return results['documents'][0]