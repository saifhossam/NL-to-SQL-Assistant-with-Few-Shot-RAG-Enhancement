# 🗄️ SQL Chat — RAG-Enhanced Text-to-SQL Assistant

A conversational interface for querying PostgreSQL databases using natural language. The system translates user questions into validated SQL queries, executes them, and returns human-readable answers — enhanced by optional few-shot examples retrieved via RAG.

---

## 🗂 Project Structure

```
SQL_CHAT/
├── app.py                  # Main Streamlit app (styled terminal UI)
├── chains.py               # LangChain chain definitions
├── config.py               # LLM setup and environment config
├── database.py             # DB connection, schema extraction, query execution
├── prompts.py              # Prompt templates (SQL gen, answer, table selector, relevance, fallback)
├── sql_generator.py        # SQL generation, fixing, and fallback suggestions
├── sql_validator.py        # SQL safety and syntax validation
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
│   SQL Generator     │  → LLM generates a PostgreSQL query using schema + examples
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   SQL Validator     │  → Blocks dangerous keywords, validates tables & syntax
└────────┬────────────┘
         │        └── on failure → Auto-correct (up to 5 retries)
         │                              └── still failing → Fallback suggestions
         ▼
┌─────────────────────┐
│   Query Executor    │  → Runs query against PostgreSQL, returns a DataFrame
└────────┬────────────┘
         │        └── > 10 rows → Limit to 10 and flag in the answer
         ▼
┌─────────────────────┐
│  Answer Generator   │  → LLM converts data into a natural language response
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

## 🛡️ SQL Validation

Before any query is executed, it passes through a two-layer validation pipeline:

1. **Forbidden keyword check** — blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`
2. **Syntax check** — runs `EXPLAIN` on the query to catch PostgreSQL syntax errors

### Auto-correction

If validation fails, the broken SQL and the exact error are sent back to the LLM to fix. This retries up to **5 times**. Each retry is shown in the UI with an amber badge.

### Fallback suggestions

If all retries are exhausted, instead of showing a raw error the system:

1. Asks the LLM to generate 2 alternative questions close in intent to the original
2. Generates a SQL query for each alternative
3. Validates each suggestion against the real database
4. Displays only the ones that pass — with the question and runnable SQL shown in expandable cards

---

## 🔒 Security & Robustness

### Off-topic question handling

A dedicated relevance check runs before SQL generation. If the question cannot be answered using the database schema — or contains a prompt injection attempt — the app shows a clear message and stops processing without calling the database.

### Large result limiting

If a query returns more than **10 rows**, the results are automatically trimmed to 10 and the answer includes a note informing the user that the output has been limited.

---

## 🔧 Configuration

| Variable | Description |
|---|---|
| `AZURE_ENDPOINT` | Endpoint for Microsoft Azure OpenAI |
| `AZURE_API_KEY` | API key for Azure inference |
| `DB_URL` | PostgreSQL connection string (SQLAlchemy format) |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |

LLM settings are in `config.py`. Embedding model settings are in `rag/embeddings.py`.

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
