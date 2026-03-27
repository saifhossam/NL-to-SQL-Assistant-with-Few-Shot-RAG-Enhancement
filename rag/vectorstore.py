import os
import json
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rag.embeddings import get_embeddings


CHROMA_PATH = "rag/chroma_store"


def build_vectorstore(data=None):
    """Build vectorstore from a list of dicts or from the default example_data.json."""
    if data is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "example_data.json")
        with open(file_path, "r") as f:
            data = json.load(f)

    documents = []
    for item in data:
        content = f"Question: {item['question']}\nSQL: {item['sql']}"
        documents.append(Document(page_content=content))

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        persist_directory=CHROMA_PATH
    )

    return vectorstore


if __name__ == "__main__":
    build_vectorstore()
    print("✅ Vectorstore built.")