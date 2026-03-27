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


def validate_tables_exist(sql_query, db_url: str = None):
    tables = list_all_tables(db_url=db_url)

    found_tables = re.findall(r'FROM\s+"?(\w+)"?|JOIN\s+"?(\w+)"?', sql_query, re.IGNORECASE)

    extracted = []
    for t1, t2 in found_tables:
        if t1:
            extracted.append(t1)
        if t2:
            extracted.append(t2)

    for table in extracted:
        if table not in tables:
            return False, f"Table '{table}' does not exist."

    return True, None


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

    # 2️⃣ Check tables
    tables_ok, message = validate_tables_exist(sql_query, db_url=db_url)
    if not tables_ok:
        return False, message

    # 3️⃣ Check syntax using EXPLAIN
    syntax_ok, message = validate_sql_syntax(sql_query, db_url=db_url)
    if not syntax_ok:
        return False, f"SQL Syntax Error: {message}"

    return True, "SQL is valid."