import os
import json
import shutil
import time
import streamlit as st
from dotenv import load_dotenv
from config import MAX_RETRIES
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

st.set_page_config(
    page_title="SQL ChatBot",
    page_icon="🗄️",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --bg-primary: #080c14;
    --bg-secondary: #0d1421;
    --bg-card: #111827;
    --bg-card-hover: #162033;
    --border: #1e2d45;
    --border-glow: #0ea5e9;
    --accent-cyan: #0ea5e9;
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
    --text-primary: #e2e8f0;
    --text-secondary: #64748b;
    --text-muted: #334155;
    --font-mono: 'JetBrains Mono', monospace;
    --font-display: 'Syne', sans-serif;
}

/* Base */
html, body, [class*="css"] {
    font-family: var(--font-mono) !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: var(--bg-primary) !important;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(14, 165, 233, 0.04) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(16, 185, 129, 0.03) 0%, transparent 50%) !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── HEADER ── */
.app-header {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}

.app-title {
    font-family: var(--font-display) !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin: 0 !important;
}

.app-title span {
    color: var(--accent-cyan);
}

.app-subtitle {
    font-family: var(--font-mono) !important;
    font-size: 0.78rem !important;
    color: var(--text-secondary) !important;
    margin-top: 0.4rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.prompt-prefix {
    color: var(--accent-green);
    font-weight: 700;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] > div {
    padding: 1.5rem 1rem !important;
}

.sidebar-section-title {
    font-family: var(--font-mono) !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--accent-cyan) !important;
    margin: 1.2rem 0 0.7rem 0 !important;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.sidebar-section-title::before {
    content: '';
    display: inline-block;
    width: 3px;
    height: 12px;
    background: var(--accent-cyan);
    border-radius: 2px;
}

.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    margin-top: 0.5rem;
}

.status-connected {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: var(--accent-green);
}

.status-disconnected {
    background: rgba(100, 116, 139, 0.1);
    border: 1px solid rgba(100, 116, 139, 0.2);
    color: var(--text-secondary);
}

.status-active {
    background: rgba(14, 165, 233, 0.1);
    border: 1px solid rgba(14, 165, 233, 0.3);
    color: var(--accent-cyan);
}

/* ── INPUT FIELDS ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1) !important;
}

[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* Main question input — larger */
.main-input [data-testid="stTextInput"] input {
    font-size: 1rem !important;
    padding: 0.85rem 1rem !important;
    border-color: var(--border-glow) !important;
    background: var(--bg-card) !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-secondary) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border-radius: 5px !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    background: rgba(14, 165, 233, 0.06) !important;
}

[data-testid="stFormSubmitButton"] > button,
.stButton > button[kind="primary"] {
    background: var(--accent-cyan) !important;
    border-color: var(--accent-cyan) !important;
    color: var(--bg-primary) !important;
    font-weight: 700 !important;
}

[data-testid="stFormSubmitButton"] > button:hover,
.stButton > button[kind="primary"]:hover {
    background: #38bdf8 !important;
    border-color: #38bdf8 !important;
    color: var(--bg-primary) !important;
    box-shadow: 0 0 16px rgba(14, 165, 233, 0.35) !important;
}

/* ── CARDS / RESULT BLOCKS ── */
.result-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0;
    position: relative;
    overflow: hidden;
}

.result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-green));
    opacity: 0.6;
}

.result-card-title {
    font-family: var(--font-mono) !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
    margin-bottom: 0.75rem !important;
}

/* ── CODE BLOCKS ── */
[data-testid="stCode"] {
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    background: #060a10 !important;
}

[data-testid="stCode"] pre {
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    border-left-width: 3px !important;
}

.stSuccess {
    background: rgba(16, 185, 129, 0.08) !important;
    border-color: var(--accent-green) !important;
    color: var(--accent-green) !important;
}

.stError {
    background: rgba(239, 68, 68, 0.08) !important;
    border-color: var(--accent-red) !important;
}

.stWarning {
    background: rgba(245, 158, 11, 0.08) !important;
    border-color: var(--accent-amber) !important;
}

.stInfo {
    background: rgba(14, 165, 233, 0.08) !important;
    border-color: var(--accent-cyan) !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 6px !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-cyan) !important;
}

[data-testid="stFileUploader"] label {
    color: var(--text-secondary) !important;
    font-size: 0.75rem !important;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] {
    color: var(--accent-cyan) !important;
}

/* ── DIVIDER ── */
hr {
    border-color: var(--border) !important;
    margin: 1rem 0 !important;
}

/* ── CAPTION ── */
[data-testid="stCaptionContainer"] {
    color: var(--text-secondary) !important;
    font-size: 0.72rem !important;
    font-family: var(--font-mono) !important;
}

/* ── STEP INDICATOR ── */
.step-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0;
    opacity: 0.5;
    transition: opacity 0.3s;
}
.step-row.active { opacity: 1; }

.step-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--text-muted);
    flex-shrink: 0;
}
.step-dot.done { background: var(--accent-green); }
.step-dot.running {
    background: var(--accent-cyan);
    box-shadow: 0 0 8px var(--accent-cyan);
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.step-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    letter-spacing: 0.04em;
}

/* ── RETRY BADGE ── */
.retry-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: var(--accent-amber);
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-family: var(--font-mono);
    letter-spacing: 0.04em;
}

.corrected-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: var(--accent-green);
    font-size: 0.7rem;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-family: var(--font-mono);
    letter-spacing: 0.04em;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-secondary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
}

[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 0.78rem !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.04em !important;
}
</style>
""", unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-title">
        <span>SQL</span> ChatBot
    </div>
    <div class="app-subtitle">
        <span class="prompt-prefix">▶</span>&nbsp; Natural language → PostgreSQL · RAG-enhanced
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:

    st.markdown("### 🗄️ SQL ChatBot")
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # — DB Connection —
    st.markdown('<div class="sidebar-section-title">Database</div>', unsafe_allow_html=True)

    default_url = os.getenv("DB_URL", "")

    db_url = st.text_input(
        "PostgreSQL URL",
        value=st.session_state.get("db_url", default_url),
        type="password",
        placeholder="postgresql://user:pass@host:port/db",
        help="Your Railway or any PostgreSQL connection URL.",
    )

    if st.button("Connect", type="primary"):
        if db_url:
            try:
                engine = get_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(__import__("sqlalchemy").text("SELECT 1"))
                st.session_state["db_url"] = db_url
                st.success("Connection established ✓")
            except Exception as e:
                st.error(f"Failed: {e}")
        else:
            st.warning("Enter a database URL first.")

    if st.session_state.get("db_url"):
        st.markdown('<span class="status-badge status-connected">● Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">○ Not connected</span>', unsafe_allow_html=True)

    st.divider()

    # — Few-Shot Upload —
    st.markdown('<div class="sidebar-section-title">Few-Shot Examples</div>', unsafe_allow_html=True)
    st.caption("Upload a JSON list of `{ question, sql }` pairs to enhance generation.")

    uploaded_file = st.file_uploader("Upload JSON", type="json", label_visibility="collapsed")

    if uploaded_file:
        try:
            data = json.load(uploaded_file)

            if not isinstance(data, list) or len(data) == 0:
                st.error("Must be a non-empty JSON array.")
            else:
                keys = list(data[0].keys())
                has_required = "question" in keys and "sql" in keys

                if has_required:
                    # Format is already correct
                    existing = st.session_state.get("examples_data", [])
                    is_append = bool(existing)

                    if is_append:
                        st.info(f"Will append {len(data)} → total {len(existing) + len(data)}")

                    label = "Append to Examples" if is_append else "Load Examples"

                    if st.button(label, type="primary"):
                        with st.spinner("Indexing..."):
                            merged = existing + data
                            vectorstore = build_vectorstore(merged)
                            st.session_state["custom_vectorstore"] = vectorstore
                            st.session_state["examples_data"] = merged
                        action = "Appended" if is_append else "Loaded"
                        st.success(f"{action} · {len(merged)} examples indexed")

                else:
                    # Let user map keys manually
                    st.warning("Fields don't match expected format. Map your keys below:")

                    col1, col2 = st.columns(2)
                    with col1:
                        question_key = st.selectbox(
                            "question →",
                            options=keys,
                            index=0,
                            key="question_key_map"
                        )
                    with col2:
                        sql_key = st.selectbox(
                            "sql →",
                            options=keys,
                            index=min(1, len(keys) - 1),
                            key="sql_key_map"
                        )

                    # Preview
                    if question_key and sql_key:
                        st.caption("Preview (first item):")
                        st.json({
                            "question": data[0].get(question_key, ""),
                            "sql": data[0].get(sql_key, "")
                        })

                    existing = st.session_state.get("examples_data", [])
                    is_append = bool(existing)
                    label = "Append to Examples" if is_append else "Load & Convert Examples"

                    if st.button(label, type="primary"):
                        converted = [
                            {
                                "question": item.get(question_key, ""),
                                "sql": item.get(sql_key, "")
                            }
                            for item in data
                            if item.get(question_key) and item.get(sql_key)
                        ]

                        if not converted:
                            st.error("No valid rows after mapping. Check your key selection.")
                        else:
                            with st.spinner("Indexing..."):
                                merged = existing + converted
                                vectorstore = build_vectorstore(merged)
                                st.session_state["custom_vectorstore"] = vectorstore
                                st.session_state["examples_data"] = merged
                            skipped = len(data) - len(converted)
                            msg = f"Loaded {len(converted)} examples"
                            if skipped:
                                msg += f" · {skipped} skipped (empty values)"
                            st.success(msg)

        except json.JSONDecodeError:
            st.error("Invalid JSON file.")

    st.divider()

    # — Add Single Example —
    st.markdown('<div class="sidebar-section-title">Add Single Example</div>', unsafe_allow_html=True)

    with st.form("add_example_form", clear_on_submit=True):
        new_question = st.text_input("Question", placeholder="e.g. Top 5 customers by revenue")
        new_sql = st.text_area("SQL Query", height=110, placeholder='SELECT ... FROM "Table" ...')
        submitted = st.form_submit_button("➕  Add Example", use_container_width=True)

        if submitted:
            if not new_question.strip() or not new_sql.strip():
                st.error("Both fields are required.")
            else:
                new_example = {"question": new_question.strip(), "sql": new_sql.strip()}
                existing = st.session_state.get("examples_data", [])
                merged = existing + [new_example]
                with st.spinner("Updating index..."):
                    vectorstore = build_vectorstore(merged)
                    st.session_state["custom_vectorstore"] = vectorstore
                    st.session_state["examples_data"] = merged
                st.success(f"Added · {len(merged)} total")

    st.divider()

    # — Status & Reset —
    if "custom_vectorstore" in st.session_state:
        count = len(st.session_state.get("examples_data", []))
        st.markdown(f'<span class="status-badge status-active">◈ {count} examples active</span>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("↺  Reset Examples"):
            del st.session_state["custom_vectorstore"]
            del st.session_state["examples_data"]
            st.rerun()
    else:
        st.markdown('<span class="status-badge status-disconnected">○ No examples — few-shot off</span>', unsafe_allow_html=True)


# ── Resolve active DB URL ──────────────────────────────────────────────────────
active_db_url = st.session_state.get("db_url", default_url)

if not active_db_url:
    st.markdown("""
    <div class="result-card" style="text-align:center; padding: 3rem 2rem;">
        <div style="font-size:2.5rem; margin-bottom:1rem">🔌</div>
        <div style="font-family:'Syne',sans-serif; font-size:1.1rem; font-weight:700; color:#e2e8f0; margin-bottom:0.5rem">
            No database connected
        </div>
        <div style="font-size:0.8rem; color:#64748b;">
            Enter your PostgreSQL URL in the sidebar to get started
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Main chat interface ────────────────────────────────────────────────────────

st.markdown('<div class="main-input">', unsafe_allow_html=True)
question = st.text_input(
    "query",
    placeholder="Ask anything about your database  →  e.g. What are the top 5 customers by total spend?",
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)
st.caption("Natural language · PostgreSQL · RAG-enhanced generation")

if question:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    total_start = time.perf_counter()
    with st.spinner(""):

        # ── Step 1: Retrieve examples ──────────────────────────────────────────
        examples = retrieve_examples(question)

        if examples:
            with st.expander("📎  Few-shot context retrieved", expanded=False):
                st.code(examples, language="text")

        # ── Step 2: Build schema ───────────────────────────────────────────────
        relevant_tables = get_relevant_tables(question, db_url=active_db_url)
        schema = get_schema(relevant_tables, db_url=active_db_url)

        # ── Step 3: Generate SQL ───────────────────────────────────────────────
        sql_query = get_sql(question, schema, examples=examples)

        # ── Step 4: Validate + auto-correct ───────────────────────────────────
        attempt = 0
        is_valid = False
        validation_message = ""

        while attempt < MAX_RETRIES:
            is_valid, validation_message = validate_sql(sql_query, db_url=active_db_url)

            if is_valid:
                break

            attempt += 1

            if attempt < MAX_RETRIES:
                st.markdown(
                    f'<div class="retry-badge">⟳ &nbsp;Auto-correcting · attempt {attempt}/{MAX_RETRIES - 1}</div>',
                    unsafe_allow_html=True,
                )
                sql_query = fix_sql(sql_query, validation_message, schema)

        # ── Generated SQL block ────────────────────────────────────────────────
        #st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-card-title">Generated SQL</div>', unsafe_allow_html=True)

        if attempt > 0 and is_valid:
            st.markdown(
                f'<div class="corrected-badge" style="margin-bottom:0.75rem">✓ &nbsp;Auto-corrected in {attempt} pass{"es" if attempt > 1 else ""}</div>',
                unsafe_allow_html=True,
            )

        st.code(sql_query, language="sql")
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Validation result ──────────────────────────────────────────────────
        if not is_valid:
            st.error(f"Validation failed after {MAX_RETRIES} attempts — {validation_message}")
            st.stop()

        st.success("SQL validated ✓")

        # ── Execute & display ──────────────────────────────────────────────────
        result = execute_sql_query(sql_query, db_url=active_db_url)

        #st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-card-title">Query Result</div>', unsafe_allow_html=True)
        st.dataframe(result, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Natural language answer ────────────────────────────────────────────
        final_answer = get_natural_response(question, result)

        total_latency = time.perf_counter() - total_start
        print(f"🚀 Total End-to-End Latency: {total_latency:.3f} seconds")

        #st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.markdown('<div class="result-card-title">Answer</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.95rem; line-height:1.7; color:#e2e8f0;">{final_answer}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)