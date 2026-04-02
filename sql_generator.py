import hashlib
import streamlit as st
from chains import sql_chain, sql_fix_chain, fallback_chain
from sql_validator import validate_sql
from rag.retriever import retrieve_examples
from config import QUERY_CACHE_ENABLED, LOG_LATENCY
import time


# ── Helpers ────────────────────────────────────────────────────────────────────

def _question_hash(question: str) -> str:
    """Return a short, stable hash for *question* used as a cache key."""
    return hashlib.md5(question.strip().lower().encode()).hexdigest()


def _cache_key(question: str) -> str:
    return f"sql_cache:{_question_hash(question)}"


# ── SQL generation (with caching) ──────────────────────────────────────────────

def get_sql(question: str, schema: str, examples=None) -> str:
    """Generate a SQL query for *question*.

    When ``QUERY_CACHE_ENABLED`` is True (config.py) and the same question was
    already answered in this session, the cached SQL is returned immediately
    without spending any LLM tokens.
    """
    if QUERY_CACHE_ENABLED:
        cached = st.session_state.get(_cache_key(question))
        if cached:
            if LOG_LATENCY:
                print(f"[sql_generator] Cache hit for: {question!r}")
            return cached

    examples = retrieve_examples(question)

    t0 = time.perf_counter()
    sql = sql_chain.invoke({
        "question": question,
        "schema": schema,
        "examples": examples or "No examples provided.",
    })
    if LOG_LATENCY:
        print(f"[sql_generator] SQL generation: {time.perf_counter() - t0:.3f}s")

    sql = sql.replace("```sql", "").replace("```", "").strip()

    if QUERY_CACHE_ENABLED:
        st.session_state[_cache_key(question)] = sql

    return sql


def invalidate_sql_cache(question: str) -> None:
    """Remove the cached SQL for *question* so the next call regenerates it.

    Call this after a successful fix so an auto-corrected query replaces the
    original cached entry.
    """
    key = _cache_key(question)
    st.session_state.pop(key, None)


# ── SQL auto-correction ────────────────────────────────────────────────────────

def fix_sql(sql_query: str, error_message: str, schema: str) -> str:
    """Ask the LLM to repair *sql_query* given the *error_message*."""
    sql = sql_fix_chain.invoke({
        "sql": sql_query,
        "error": error_message,
        "schema": schema,
    })
    return sql.replace("```sql", "").replace("```", "").strip()


# ── Fallback suggestions ───────────────────────────────────────────────────────

def get_fallback_suggestions(
    question: str, schema: str, db_url: str = None
) -> list[dict]:
    """Ask the LLM for 2 alternative questions + validated SQL queries.

    Only suggestions whose SQL passes ``validate_sql`` are included.

    Returns
    -------
    list of ``{"question": str, "sql": str}``
    """
    raw = fallback_chain.invoke({
        "question": question,
        "schema": schema,
    }).strip()

    suggestions = []
    for i in (1, 2):
        try:
            q_key = f"SUGGESTION_{i}_QUESTION:"
            s_key = f"SUGGESTION_{i}_SQL:"

            q_start = raw.index(q_key) + len(q_key)
            s_start = raw.index(s_key) + len(s_key)
            q_end = raw.index(s_key)
            next_key = f"SUGGESTION_{i + 1}_QUESTION:"
            s_end = raw.index(next_key) if next_key in raw else len(raw)

            alt_question = raw[q_start:q_end].strip()
            alt_sql = (
                raw[s_start:s_end].strip()
                .replace("```sql", "")
                .replace("```", "")
                .strip()
            )

            is_valid, _ = validate_sql(alt_sql, db_url=db_url)
            if is_valid:
                suggestions.append({"question": alt_question, "sql": alt_sql})
        except (ValueError, IndexError):
            continue

    return suggestions