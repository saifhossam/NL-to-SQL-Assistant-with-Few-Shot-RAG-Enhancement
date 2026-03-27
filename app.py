import os
import json
import shutil
import streamlit as st
from dotenv import load_dotenv
from database import get_schema, execute_sql_query, get_engine
from table_selector import get_relevant_tables
from sql_generator import get_sql, fix_sql
from answer_generator import get_natural_response
from sql_validator import validate_sql
from rag.retriever import retrieve_examples
from rag.vectorstore import build_vectorstore, CHROMA_PATH

load_dotenv()

if "session_initialized" not in st.session_state:
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    st.session_state["session_initialized"] = True

st.set_page_config(page_title="SQL ChatBot")
st.title("Chat with PostgreSQL DB")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:

    # — DB Connection —
    st.header("🔌 Database Connection")
    default_url = os.getenv("DB_URL", "")

    db_url = st.text_input(
        "PostgreSQL URL",
        value=st.session_state.get("db_url", default_url),
        type="password",
        placeholder="postgresql://user:pass@host:port/db",
        help="Paste your Railway (or any PostgreSQL) connection URL here.",
    )

    if st.button("Connect", type="primary"):
        if db_url:
            try:
                engine = get_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(__import__("sqlalchemy").text("SELECT 1"))
                st.session_state["db_url"] = db_url
                st.success("Connected ✅")
            except Exception as e:
                st.error(f"Connection failed: {e}")
        else:
            st.warning("Please enter a database URL.")

    if st.session_state.get("db_url"):
        st.caption("🟢 Connected")
    else:
        st.caption("🔴 Not connected")

    st.divider()

    # — Few-Shot Examples Upload —
    st.header("📂 Few-Shot Examples")
    st.caption("Optional: upload a JSON file with `question` and `sql` fields to enable few-shot enhancement.")

    uploaded_file = st.file_uploader("Upload examples JSON", type="json")

    if uploaded_file:
        try:
            data = json.load(uploaded_file)

            if not isinstance(data, list):
                st.error("JSON must be a list of objects.")
            elif not all("question" in item and "sql" in item for item in data):
                st.error('Each object must have "question" and "sql" fields.')
            else:
                existing = st.session_state.get("examples_data", [])
                is_append = bool(existing)

                if is_append:
                    st.info(f"This will append {len(data)} examples to the existing {len(existing)}.")

                label = "Append Examples" if is_append else "Load Examples"

                if st.button(label, type="primary"):
                    with st.spinner("Building vectorstore..."):
                        merged = existing + data
                        vectorstore = build_vectorstore(merged)
                        st.session_state["custom_vectorstore"] = vectorstore
                        st.session_state["examples_data"] = merged
                    st.success(f"{'Appended' if is_append else 'Loaded'} — {len(merged)} total examples ✅")

        except json.JSONDecodeError:
            st.error("Invalid JSON file.")

    st.divider()

    # — Add Single Example —
    st.subheader("➕ Add Single Example")

    with st.form("add_example_form", clear_on_submit=True):
        new_question = st.text_input("Question")
        new_sql = st.text_area("SQL Query", height=100)
        submitted = st.form_submit_button("Add Example")

        if submitted:
            if not new_question.strip() or not new_sql.strip():
                st.error("Both fields are required.")
            else:
                new_example = {"question": new_question.strip(), "sql": new_sql.strip()}
                existing = st.session_state.get("examples_data", [])
                merged = existing + [new_example]

                with st.spinner("Updating vectorstore..."):
                    vectorstore = build_vectorstore(merged)
                    st.session_state["custom_vectorstore"] = vectorstore
                    st.session_state["examples_data"] = merged

                st.success(f"Example added — {len(merged)} total examples ✅")

    st.divider()

    if "custom_vectorstore" in st.session_state:
        count = len(st.session_state.get("examples_data", []))
        st.caption(f"🟢 Few-shot active — {count} examples loaded")
        if st.button("Reset"):
            del st.session_state["custom_vectorstore"]
            del st.session_state["examples_data"]
            st.rerun()
    else:
        st.caption("⚪ No examples uploaded — running without few-shot")

# ── Resolve active DB URL ──────────────────────────────────────────────────────
active_db_url = st.session_state.get("db_url", default_url)

if not active_db_url:
    st.info("👈 Enter your PostgreSQL URL in the sidebar to get started.")
    st.stop()

# ── Main chat interface ────────────────────────────────────────────────────────
MAX_RETRIES = 3

question = st.text_input("Ask a question about the database")

if question:
    with st.spinner("Thinking..."):

        examples = retrieve_examples(question)

        if examples:
            st.subheader("Retrieved Similar Examples (Few-Shot Context)")
            st.code(examples)

        relevant_tables = get_relevant_tables(question, db_url=active_db_url)
        schema = get_schema(relevant_tables, db_url=active_db_url)

        sql_query = get_sql(question, schema, examples=examples)

        attempt = 0
        is_valid = False
        validation_message = ""

        while attempt < MAX_RETRIES:
            is_valid, validation_message = validate_sql(sql_query, db_url=active_db_url)

            if is_valid:
                break

            attempt += 1

            if attempt < MAX_RETRIES:
                st.warning(f"Attempt {attempt}: SQL invalid — retrying with error feedback...")
                sql_query = fix_sql(sql_query, validation_message, schema)

        st.subheader("Generated SQL")
        if attempt > 0 and is_valid:
            st.caption(f"✏️ Auto-corrected after {attempt} attempt(s)")
        st.code(sql_query, language="sql")

        if not is_valid:
            st.error(f"SQL Validation Failed after {MAX_RETRIES} attempts: {validation_message}")
        else:
            st.success("SQL Validation Passed ✅")

            result = execute_sql_query(sql_query, db_url=active_db_url)

            st.subheader("SQL Result")
            st.write(result)

            final_answer = get_natural_response(question, result)

            st.subheader("Answer")
            st.write(final_answer)