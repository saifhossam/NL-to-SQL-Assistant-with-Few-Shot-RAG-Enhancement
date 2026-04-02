import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()


# ── Retry / display limits ─────────────────────────────────────────────────────
MAX_RETRIES = 5      # Max number of retries before applying the fallback
ROW_LIMIT = 10       # Number of rows shown when a query returns a large result set

# ── Schema caching ─────────────────────────────────────────────────────────────
# How many seconds a fetched schema stays valid before being re-fetched.
# Set to 0 to disable caching and always fetch fresh.
SCHEMA_CACHE_TTL = 300  # 5 minutes

# ── Query result caching ───────────────────────────────────────────────────────
# When True, identical natural-language questions skip the LLM and return the
# cached SQL from the previous run (within the same Streamlit session).
QUERY_CACHE_ENABLED = True

# ── Performance logging ────────────────────────────────────────────────────────
# When True, per-step and total latencies are printed to stdout.
LOG_LATENCY = True

# ── Embedding Model ────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384

# ── Qdrant Setup ───────────────────────────────────────────────────────────────
COLLECTION_NAME = "few_shot_examples"
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# ── Azure Settings ─────────────────────────────────────────────────────────────
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
LLM_MODEL = "gpt-4.1-mini"


_llm_instance = None

def get_llm():
    """Return a singleton AzureChatOpenAI instance."""
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