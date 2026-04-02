import pandas as pd
from chains import answer_chain


def get_natural_response(question: str, data, is_limited: bool = False) -> str:
    """Return a natural-language answer for *question* based on *data*.

    Parameters
    ----------
    question   : the original user question
    data       : a ``pd.DataFrame`` with query results, or an error string
    is_limited : True when the DataFrame was trimmed to ROW_LIMIT rows

    Edge cases handled
    ------------------
    * *data* is a string  → SQL execution error; return a user-friendly message
      instead of passing raw SQL errors to the LLM.
    * *data* is an empty DataFrame → return a concise "no results" message
      without wasting a token budget on an LLM call.
    """
    # Guard: SQL execution returned an error string
    if isinstance(data, str):
        return (
            "⚠️ The query could not be executed due to a database error. "
            "Please review the generated SQL and try again."
        )

    # Guard: query ran fine but returned zero rows
    if isinstance(data, pd.DataFrame) and data.empty:
        return (
            "The query executed successfully but returned **no results**. "
            "This could mean the data you're looking for doesn't exist "
            "in the database, or the filter conditions are too restrictive."
        )

    return answer_chain.invoke({
        "question": question,
        "data": data.to_string(index=False),
        "is_limited": str(is_limited),
    }).strip()