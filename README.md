# 🗄️ SQL Chat — RAG-Enhanced Text-to-SQL Assistant

A conversational interface for querying PostgreSQL databases using natural language. The system translates user questions into validated SQL queries, executes them, and returns human-readable answers — enhanced by few-shot examples retrieved via RAG.

---

## 🗂 Project Structure

```
SQL_C_/
├── app.py                  # Main Streamlit app entry point
├── app_langchain.py        # Alternative LangChain-based app
├── chains.py               # LangChain chain definitions (SQL, answer, table selector)
├── config.py               # LLM setup and environment config
├── database.py             # DB connection, schema extraction, query execution
├── prompts.py              # Prompt templates (SQL gen, answer, table selector)
├── sql_generator.py        # Orchestrates SQL generation with RAG examples
├── sql_validator.py        # SQL safety and syntax validation
├── table_selector.py       # Selects relevant tables for a given question
├── answer_generator.py     # Converts SQL results to natural language answers
├── test_latency.py         # Check the latency of the LLM
├── rag/
│   ├── embeddings.py       # HuggingFace embedding model
│   ├── vectorstore.py      # Builds ChromaDB vectorstore from few-shot examples
│   ├── retriever.py        # Retrieves relevant few-shot examples for a question
│   ├── example_data.json   # Few-shot Q&A SQL examples
│   └── chroma_store/       # Persisted ChromaDB vector store
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
┌─────────────────┐
│  Table Selector │  → Picks only the relevant tables from the DB
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RAG Retriever  │  → Fetches the 3 most similar few-shot SQL examples
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQL Generator  │  → LLM generates a PostgreSQL query using schema + examples
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQL Validator  │  → Blocks dangerous keywords, validates tables & syntax
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Query Executor │  → Runs the query against PostgreSQL, returns a DataFrame
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Answer Generator│  → LLM converts the data into a natural language response
└─────────────────┘
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone [<your-repo-url>](https://github.com/Ahmed-Essam-Hammam/Text-to-SQL-Assistant-with-Few-Shot-RAG-Enhancement.git)
cd SQL_C_
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
DB_URL=postgresql://user:password@host:port/dbname     # This could also be added to the Streamlit user interface
```

### 5. Run the app

```bash
streamlit run app.py
```

### 6. Add your database link

```bash
If you already done that in the .env file, it will be used as default, it can be changed though.
```

### 7. Upload a JSON file of examples of your database (optional)

---

## 🧠 Few-Shot RAG Enhancement

The system uses a local ChromaDB vector store to store the embedded example question-SQL pairs:

```json
[
  {
    "question": "How many customers are in Brazil?",
    "sql": "SELECT COUNT(*) FROM \"Customer\" WHERE \"Country\" = 'Brazil';"
  }
]
```

At query time, the 3 most semantically similar examples are retrieved and injected into the SQL generation prompt — significantly improving accuracy for domain-specific or complex queries.

To add your own examples, upload a JSON file to the Streamlit interface.

---

## 🛡️ SQL Validation

Before any query is executed, it passes through a three-layer validation pipeline:

1. **Forbidden keyword check** — blocks `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`
2. **Table existence check** — verifies all referenced tables exist in the database
3. **Syntax check** — runs `EXPLAIN` on the query to catch PostgreSQL syntax errors

---

## 🔧 Configuration

| Variable | Description |
|---|---|
| `AZURE_ENDPOINT` | Endpoint for Microsoft Azure |
| `AZURE_API_KEY` | API key for Azure inference |
| `DB_URL` | PostgreSQL connection string (SQLAlchemy format) |

LLM and embedding settings are in `config.py` and `rag/embeddings.py`.

---

## 🧰 Tech Stack

- **[LangChain](https://www.langchain.com/)** — Chain orchestration and prompt management
- **[ChromaDB](https://www.trychroma.com/)** — Local vector store for few-shot examples
- **[HuggingFace](https://huggingface.co/)** — `all-MiniLM-L6-v2` for example embeddings
- **[Microsoft Azure](https://portal.azure.com/)** — LLM inference (OpenAI-compatible API)
- **[PostgreSQL](https://www.postgresql.org/)** — Target database
- **[SQLAlchemy](https://www.sqlalchemy.org/)** — Database connection and query execution
- **[Streamlit](https://streamlit.io/)** — Web interface

---

## 📝 Notes

- The LLM is instructed to always double-quote PostgreSQL identifiers that contain capital letters to prevent case-folding issues.
- The schema inspector automatically fetches column names, data types, and sample values to give the LLM rich context.
- If no relevant tables are found by the table selector, the full schema is used as a fallback.
