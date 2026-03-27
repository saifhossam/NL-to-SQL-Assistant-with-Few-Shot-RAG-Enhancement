import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


MAX_RETRIES = 3

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
LLM_MODEL = "gpt-4.1-mini"


_llm_instance = None

def get_llm():
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = AzureChatOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=AZURE_API_KEY,
            api_version="2024-12-01-preview",
            deployment_name=LLM_MODEL,
            temperature=0
        )

    return _llm_instance
