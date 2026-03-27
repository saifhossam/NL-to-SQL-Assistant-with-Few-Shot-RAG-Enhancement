from chains import table_selector_chain
from database import list_all_tables


def get_relevant_tables(question, db_url: str = None):

    tables = list_all_tables(db_url=db_url)

    response = table_selector_chain.invoke({
        "question": question,
        "tables": tables
    })

    filtered = [
        t.strip() for t in response.split(",")
        if t.strip() in tables
    ]

    if not filtered:
        return tables

    return filtered