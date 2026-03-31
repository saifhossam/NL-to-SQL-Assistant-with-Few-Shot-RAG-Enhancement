import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


MAX_RETRIES = 5      # Max number of retries before applying the fallback
ROW_LIMIT = 10       # Number of rows will be shown if the generated SQL query outputs a large number of records


# Embedding Model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384


# Qdrant Setup
COLLECTION_NAME = "few_shot_examples"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


# Azure Settings
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
