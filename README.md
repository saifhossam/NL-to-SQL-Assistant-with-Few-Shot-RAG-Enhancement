# 🗄️ SQL Chat — RAG-Enhanced Text-to-SQL Assistant

A conversational interface for querying PostgreSQL databases using natural language. The system translates user questions into validated SQL queries, executes them, and returns human-readable answers — enhanced by optional few-shot examples retrieved via RAG.

---

## 🗂 Project Structure

```
SQL_CHAT/
├── app.py                  # Main Streamlit app (styled terminal UI)
├── chains.py               # LangChain chain definitions + safe_invoke() injection guard
├── config.py               # LLM setup, environment config, and feature flags
├── database.py             # DB connection, TTL-cached schema extraction, query execution
├── prompts.py              # Prompt templates (SQL gen, answer, table selector, relevance, fallback)
├── sql_generator.py        # SQL generation with in-memory caching, fixing, and fallback suggestions
├── sql_validator.py        # SQL safety, syntax validation, and complexity warnings
├── table_selector.py       # Selects relevant tables for a given question
├── answer_generator.py     # Converts SQL results to natural language answers
├── test_latency.py         # Check the latency of the LLM
├── rag/
│   ├── embeddings.py       # HuggingFace embedding model
│   ├── vectorstore.py      # Builds Qdrant Cloud vectorstore from few-shot examples
│   └── retriever.py        # Retrieves relevant few-shot examples for a question
├── requirements.txt
├── .env
└── .env.example
```

---

## ⚙️ How It Works

```
    User Question
         │
         ▼
┌─────────────────────┐
│  Injection Guard    │  → Screens input for prompt-injection patterns before any LLM call
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Relevance Check    │  → Blocks off-topic questions
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Table Selector    │  → Picks only the relevant tables from the DB schema
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   RAG Retriever     │  → Fetches 3 most similar few-shot examples (if uploaded)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Schema Fetcher    │  → Retrieves schema with TTL caching (default: 5 min)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   SQL Generator     │  → LLM generates a PostgreSQL query (cached by question hash)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   SQL Validator     │  → Blocks dangerous keywords, validates syntax via EXPLAIN
└────────┬────────────┘       └── Non-blocking complexity warnings (SELECT *, no LIMIT, etc.)
         │        └── on failure → Auto-correct (up to 5 retries, cache invalidated each time)
         │                              └── still failing → Fallback suggestions
         ▼
┌─────────────────────┐
│   Query Executor    │  → Runs query against PostgreSQL, returns a DataFrame
└────────┬────────────┘
         │        └── > 10 rows → Limit to 10 and flag in the answer
         ▼
┌─────────────────────┐
│  Answer Generator   │  → LLM converts data into a natural language response
└────────┬────────────┘       └── Guards: empty DataFrame & SQL error strings handled without LLM call
         │
         ▼
┌─────────────────────┐
│  Timing + History   │  → Per-step latency displayed in UI; query logged to history panel
└─────────────────────┘
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Ahmed-Essam-Hammam/Text-to-SQL-Assistant-with-Few-Shot-RAG-Enhancement
cd SQL_CHAT
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
AZURE_ENDPOINT=your_azure_endpoint_here
AZURE_API_KEY=your_azure_api_key_here
DB_URL=postgresql://user:password@host:port/dbname

QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

### 6. Connect your database

Enter your PostgreSQL connection URL in the sidebar. If `DB_URL` is set in `.env`, it will be pre-filled but can be changed at any time.

### 7. Upload few-shot examples (optional)

Upload a JSON file of question-SQL pairs through the sidebar to enable RAG-enhanced generation.

---

## 🧠 Few-Shot RAG Enhancement

Few-shot enhancement is **fully optional**. If no examples are uploaded, the system runs without them. When examples are provided, the 3 most semantically similar ones are retrieved from Qdrant Cloud and injected into the SQL generation prompt.

### JSON format

```json
[
  {
    "question": "How many customers are in Brazil?",
    "sql": "SELECT COUNT(*) FROM \"Customer\" WHERE \"Country\" = 'Brazil';"
  }
]
```

### Custom key mapping

If your JSON file uses different field names (e.g. `query` instead of `question`), the app detects this automatically and lets you map your keys to the required format via a dropdown — no manual reformatting needed.

### Managing examples in the UI

The sidebar provides three ways to manage few-shot examples:

- **Upload a JSON file** — load or append a batch of examples
- **Add a single example** — enter a question and SQL query directly in the UI
- **Append across uploads** — each new upload is merged with the existing examples; the vectorstore is rebuilt from the full combined set
- **Reset** — clears all examples and deletes the Qdrant collection

> The Qdrant collection is also automatically cleared when a new session starts, ensuring a clean state.

---

## 🛡️ SQL Validation & Safety

Before any query is executed, it passes through a multi-layer validation and safety pipeline:

1. **Prompt injection guard** — `safe_invoke()` in `chains.py` screens every user input against regex patterns that detect attempts to override system instructions (e.g. "ignore previous instructions", "you are now…"). Flagged inputs return a sentinel value immediately — no LLM tokens are spent.
2. **Forbidden keyword check** — blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`
3. **Syntax check** — runs `EXPLAIN` on the query to catch PostgreSQL syntax errors
4. **Complexity warnings** — non-blocking advisory checks surfaced in the UI:
   - `SELECT *` with no column projection
   - Missing `WHERE` on non-aggregate queries (potential full-table scan)
   - Missing `LIMIT` on non-aggregate queries (potentially huge result sets)
   - Multiple leading-wildcard `LIKE '%…'` patterns (index-unfriendly)
   - Cartesian product detected (comma-joined tables with no condition)

### Auto-correction

If validation fails, the broken SQL and the exact error are sent back to the LLM to fix. The fix prompt now includes a step-by-step chain-of-thought instruction to improve repair quality. This retries up to **5 times**. The SQL cache is invalidated on each retry so a fresh query is generated. Each retry is shown in the UI with an amber badge.

### Fallback suggestions

If all retries are exhausted, instead of showing a raw error the system:

1. Asks the LLM to generate 2 alternative questions close in intent to the original
2. Generates a SQL query for each alternative
3. Validates each suggestion against the real database
4. Displays only the ones that pass — with the question and runnable SQL shown in expandable cards

---

## ⚡ Performance Optimisations

### Schema caching (TTL-based)

`get_schema()` in `database.py` caches fetched schemas in `st.session_state` for `SCHEMA_CACHE_TTL` seconds (default: 300 s). Repeated questions on the same set of tables skip the `information_schema` round-trip entirely until the cache expires. Set `SCHEMA_CACHE_TTL = 0` in `config.py` to disable.

### SQL query caching

When `QUERY_CACHE_ENABLED = True` (default), `get_sql()` in `sql_generator.py` computes an MD5 hash of the normalised question and stores the generated SQL in `st.session_state`. Identical follow-up questions return the cached SQL instantly with zero LLM calls. The cache entry is automatically invalidated when auto-correction runs, so a repaired query always replaces the stale one.

### Connection pooling

The SQLAlchemy engine is created with `pool_pre_ping=True` (silently drops stale connections before use) and `pool_recycle=1800` (recycles connections every 30 minutes) to prevent connection-timeout errors on long-running sessions.

---

## 📊 UI Enhancements

### Per-step timing display

Every pipeline step is timed independently and displayed after each response as a `⏱ X.XXs total` badge. Clicking `breakdown ▾` expands a table showing the latency for each step (RAG retrieval, table selection, schema fetch, relevance check, SQL generation, validation + fix, query execution, answer generation).

### CSV download

A **⬇ Download CSV** button appears below the results dataframe whenever the query returns data, allowing users to export results with one click.

### Query history panel

The sidebar shows the last 10 successful questions with their row counts. A **Clear History** button resets the list. Consecutive duplicate questions are suppressed.

---

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `AZURE_ENDPOINT` | — | Endpoint for Microsoft Azure OpenAI |
| `AZURE_API_KEY` | — | API key for Azure inference |
| `DB_URL` | — | PostgreSQL connection string (SQLAlchemy format) |
| `QDRANT_URL` | — | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | — | Qdrant Cloud API key |
| `SCHEMA_CACHE_TTL` | `300` | Seconds before a cached schema is refreshed (0 = disabled) |
| `QUERY_CACHE_ENABLED` | `True` | Cache generated SQL by question hash to skip duplicate LLM calls |
| `LOG_LATENCY` | `True` | Print per-step and total latency to stdout |
| `MAX_RETRIES` | `5` | Max auto-correction attempts before triggering fallback |
| `ROW_LIMIT` | `10` | Max rows shown when a query returns a large result set |

LLM settings (`LLM_MODEL`, `AZURE_ENDPOINT`) are in `config.py`. Embedding model settings are in `rag/embeddings.py`.

---

## 🧰 Tech Stack

- **[LangChain](https://www.langchain.com/)** — Chain orchestration and prompt management
- **[Qdrant Cloud](https://qdrant.tech/)** — Cloud vector store for few-shot example embeddings
- **[HuggingFace](https://huggingface.co/)** — `all-MiniLM-L6-v2` for semantic embeddings
- **[Microsoft Azure](https://portal.azure.com/)** — LLM inference (OpenAI-compatible API)
- **[PostgreSQL](https://www.postgresql.org/)** — Target database
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — Database connection and query execution
- **[Streamlit](https://streamlit.io/)** — Web interface

---

## 📝 Notes

- The LLM is instructed to always double-quote PostgreSQL identifiers that contain capital letters to prevent case-folding issues.
- The schema inspector automatically fetches column names, data types, and sample values to give the LLM rich context.
- If no relevant tables are found by the table selector, the full schema is used as a fallback.
- Few-shot examples are stored only in memory and in Qdrant Cloud — no local files are created or modified.
- `safe_invoke()` screens inputs before every LLM call that accepts user text, not just the table selector.