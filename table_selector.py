from chains import table_selector_chain, safe_invoke
from database import list_all_tables


def get_relevant_tables(question: str, db_url: str = None):
    """Return the subset of database tables relevant to *question*.

    Uses ``safe_invoke`` to screen the question for prompt-injection before
    sending it to the LLM.  If injection is detected, the sentinel string
    ``"__INJECTION__"`` is returned so the caller can surface a warning.

    If the LLM returns table names that are not in the actual schema (e.g. it
    hallucinated), they are silently dropped.  If *all* returned names are
    invalid (empty filtered list), every table is returned as a safe fallback.
    """
    tables = list_all_tables(db_url=db_url)

    response = safe_invoke(
        table_selector_chain,
        {"question": question, "tables": tables},
        fallback="__INJECTION__",
    )

    if response == "__INJECTION__":
        return "__INJECTION__"

    filtered = [
        t.strip()
        for t in response.split(",")
        if t.strip() in tables
    ]

    # Fall back to all tables when the LLM returned nothing usable
    return filtered if filtered else tables