import streamlit as st


def get_retriever():
    if "custom_vectorstore" in st.session_state:
        vectorstore = st.session_state["custom_vectorstore"]
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    return None


def retrieve_examples(question):
    retriever = get_retriever()

    if retriever is None:
        return None
    
    docs = retriever.invoke(question)
    return "\n\n".join([doc.page_content for doc in docs])
