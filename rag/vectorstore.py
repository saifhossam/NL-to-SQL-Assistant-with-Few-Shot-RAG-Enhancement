import os
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from rag.embeddings import get_embeddings
from config import COLLECTION_NAME, VECTOR_SIZE, QDRANT_API_KEY, QDRANT_URL




def get_qdrant_client():
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )


def build_vectorstore(data):
    """Build vectorstore in Qdrant Cloud from a list of {question, sql} dicts."""
    client = get_qdrant_client()

    # Always recreate the collection to avoid stale data
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
    )


    documents = [
        Document(page_content=f"Question: {item['question']}\nSQL: {item['sql']}")
        for item in data
    ]


    vectorstore = QdrantVectorStore.from_documents(
        documents=documents,
        embedding=get_embeddings(),
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME
    )


    return vectorstore


def clear_vectorstore():
    """Delete the collection — called on session start."""
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in collections:
        client.delete_collection(COLLECTION_NAME)
