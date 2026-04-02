import re
from sqlalchemy import text
from database import get_engine, list_all_tables


FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]


# ── Forbidden-keyword check ────────────────────────────────────────────────────

def contains_forbidden_keywords(sql_query: str) -> tuple[bool, str | None]:
    upper_sql = sql_query.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            return True, f"Forbidden keyword detected: {keyword}"
    return False, None


# ── Syntax check via EXPLAIN ───────────────────────────────────────────────────

def validate_sql_syntax(sql_query: str, db_url: str = None) -> tuple[bool, str | None]:
    engine = get_engine(db_url=db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"EXPLAIN {sql_query}"))
        return True, None
    except Exception as e:
        return False, str(e)


# ── Complexity / safety warnings ───────────────────────────────────────────────

def get_complexity_warnings(sql_query: str) -> list[str]:
    """Return a list of human-readable advisory warnings for *sql_query*.

    These are non-blocking — validation still passes — but they are surfaced
    in the UI so the user is aware of potentially expensive or risky patterns.

    Checks
    ------
    1. ``SELECT *``  — fetches all columns; unnecessary columns waste bandwidth.
    2. No ``WHERE`` clause on a non-aggregated query — may scan the full table.
    3. No ``LIMIT`` on a non-aggregated query — can return millions of rows.
    4. Multiple unindexed ``LIKE '%…'`` — leading-wildcard patterns skip indexes.
    5. Cartesian product (``FROM a, b`` with no join condition) — exponential rows.
    """
    warnings: list[str] = []
    upper = sql_query.upper()

    # 1. SELECT *
    if re.search(r"SELECT\s+\*", upper):
        warnings.append(
            "SELECT * fetches all columns — consider naming only the columns you need."
        )

    # 2 & 3. Only flag when there is no GROUP BY / aggregate (i.e. not an aggregation query)
    is_aggregate = bool(
        re.search(r"\b(GROUP\s+BY|COUNT\s*\(|SUM\s*\(|AVG\s*\(|MIN\s*\(|MAX\s*\()\b", upper)
    )
    if not is_aggregate:
        if not re.search(r"\bWHERE\b", upper):
            warnings.append(
                "No WHERE clause detected — this query may scan the entire table."
            )
        if not re.search(r"\bLIMIT\b", upper):
            warnings.append(
                "No LIMIT clause detected — large tables could return many rows."
            )

    # 4. Leading-wildcard LIKE patterns
    leading_wildcards = re.findall(r"LIKE\s+'%[^']+", upper)
    if len(leading_wildcards) >= 2:
        warnings.append(
            "Multiple leading-wildcard LIKE patterns detected — these cannot use indexes and may be slow."
        )

    # 5. Cartesian product: comma-separated tables in FROM with no JOIN/WHERE
    from_clause = re.search(r"\bFROM\b(.+?)(?:\bWHERE\b|\bGROUP\b|\bORDER\b|\bLIMIT\b|$)", upper, re.DOTALL)
    if from_clause:
        from_body = from_clause.group(1)
        has_comma_join = "," in from_body and not re.search(r"\bJOIN\b", upper)
        has_where = bool(re.search(r"\bWHERE\b", upper))
        if has_comma_join and not has_where:
            warnings.append(
                "Possible Cartesian product: multiple tables in FROM with no JOIN/WHERE condition."
            )

    return warnings


# ── Main validation entry-point ────────────────────────────────────────────────

def validate_sql(sql_query: str, db_url: str = None) -> tuple[bool, str]:
    """Validate *sql_query* and return ``(is_valid, message)``.

    Steps
    -----
    1. Block forbidden DML/DDL keywords.
    2. Check syntax with ``EXPLAIN``.

    Complexity warnings are separate (see ``get_complexity_warnings``) and do
    not affect the return value.
    """
    # 1. Block dangerous queries
    forbidden, message = contains_forbidden_keywords(sql_query)
    if forbidden:
        return False, message

    # 2. Syntax check
    syntax_ok, message = validate_sql_syntax(sql_query, db_url=db_url)
    if not syntax_ok:
        return False, f"SQL Syntax Error: {message}"

    return True, "SQL is valid."