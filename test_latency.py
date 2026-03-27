import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
import time

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
#LLM_MODEL = "gpt-4.1-mini"
LLM_MODEL = "gpt-4.1"


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




def measure_latency(llm, prompt: str):
    start_time = time.perf_counter()  

    response = llm.invoke(prompt)

    end_time = time.perf_counter()

    latency = end_time - start_time

    print(f"Response: {response.content}")
    print(f"Latency: {latency:.3f} seconds")

    return latency


# Usage
llm = get_llm()
measure_latency(llm, "Explain what are LLMs.")
