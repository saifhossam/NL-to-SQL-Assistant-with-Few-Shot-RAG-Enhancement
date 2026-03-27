import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv()


def get_engine(db_url: str):
    """Create (or retrieve cached) engine for the given DB URL."""
    # We use a session-state cache keyed by URL so switching URLs recreates the engine
    if "db_engine" not in st.session_state or st.session_state.get("db_url_used") != db_url:
        st.session_state["db_engine"] = create_engine(db_url)
        st.session_state["db_url_used"] = db_url
    return st.session_state["db_engine"]


def list_all_tables(db_url: str):
    engine = get_engine(db_url)
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public';
    """)
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
    return [row[0] for row in result]


def get_schema(selected_tables=None, db_url: str = None):
    engine = get_engine(db_url)

    if not selected_tables:
        selected_tables = list_all_tables(db_url)

    schema_str = ""

    with engine.connect() as conn:
        for table in selected_tables:
            schema_str += f"\n\nTable: {table}\n"

            column_query = text(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            """)

            columns = conn.execute(column_query).fetchall()

            for column_name, data_type in columns:
                sample_query = text(f"""
                    SELECT "{column_name}"
                    FROM "{table}"
                    WHERE "{column_name}" IS NOT NULL
                    LIMIT 3;
                """)
                try:
                    samples = conn.execute(sample_query).fetchall()
                    samples = [str(s[0]) for s in samples]
                    sample_text = ", ".join(samples)
                except:
                    sample_text = "N/A"

                schema_str += (
                    f"- {column_name} ({data_type}) "
                    f"→ samples: {sample_text}\n"
                )

    return schema_str


def execute_sql_query(sql_query: str, db_url: str = None):
    engine = get_engine(db_url)
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        return f"SQL Execution Error: {e}"