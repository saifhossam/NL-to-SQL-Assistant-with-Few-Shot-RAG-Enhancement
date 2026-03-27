import re
from sqlalchemy import text
from database import get_engine, list_all_tables


FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]


def contains_forbidden_keywords(sql_query):
    upper_sql = sql_query.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper_sql:
            return True, f"Forbidden keyword detected: {keyword}"
    return False, None



def validate_sql_syntax(sql_query, db_url: str = None):
    engine = get_engine(db_url=db_url)

    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {sql_query}"))
        return True, None
    except Exception as e:
        return False, str(e)


def validate_sql(sql_query, db_url: str = None):
    # 1️⃣ Block dangerous queries
    forbidden, message = contains_forbidden_keywords(sql_query)
    if forbidden:
        return False, message


    # 2️⃣ Check syntax using EXPLAIN
    syntax_ok, message = validate_sql_syntax(sql_query, db_url=db_url)
    if not syntax_ok:
        return False, f"SQL Syntax Error: {message}"

    return True, "SQL is valid."
