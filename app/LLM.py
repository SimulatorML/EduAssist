import requests
import json
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

FOLDER_ID = os.getenv('FOLDER_ID')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')


class YandexLLM:
    
    # TODO: add model url, temperature, max_tokens, sync and async mod
    def __init__(
        self, 
        FOLDER_ID, 
        YANDEX_API_KEY, 
        url=None
    ):
        self.folder_id = FOLDER_ID
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion" if url is None else url


    def answer(
        self, 
        messages: List[Dict[str, str]]=[], 
        message: str="", 
        nearest: str=""
    ) -> str:
        """
        messages: List[Dict[str, str]] 
        """

        prompt = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "600"
            }, 
            "messages": messages + [
                {
                    "role": "user",
                    "text": message + "\n" + nearest
                }
            ]
        }

        response = requests.post(self.url, headers=self.headers, json=prompt)
        result = response.text

        return json.loads(result)["result"]["alternatives"][0]["message"]


def llm_type(
        company: str='yandex',
        model_name: str=''
):
    if company == "yandex":
        return YandexLLM(FOLDER_ID, YANDEX_API_KEY)