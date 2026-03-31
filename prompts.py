from langchain_core.prompts import PromptTemplate


# Relevance check 
relevance_prompt = PromptTemplate(
    input_variables=["question", "schema"],
    template="""
You are a database assistant gatekeeper.

Your task is to determine whether a user's question is relevant to the given database schema, don't be so strict

A question is considered relevant if:
- It refers to data that could exist in the databse (tables, columns, relationships, values inside the database).
- If you find in the question anything that is related to the schema like (table names, column names, relationships, values that could be in the database), then this query is relevant
- Questions like this is relevant, as you notice the question contains names of tables and potential values that could exist in records or columns
    - Find the names of customers who have bought tracks from every genre available in the 'Jazz' category.
    - Find all artists who have tracks in both the '90's Gold' and 'Music' playlists.
    - Find tracks that share the exact same name but belong to different artists.


A question is NOT relevant if:
- It asks about general knowledge that is completely unrelated to the database, like "What is the largest ocean in the world".

Database Schema:
{schema}

User Question:
{question}

RULES:
- Respond with exactly one word: YES or NO.
- Respond YES only if the question can be clearly and validly answered using the schema.
- Otherwise respond NO.
- Do NOT explain your answer.
- Do NOT add punctuation.
"""
)


# Table selector 
table_selector_prompt = PromptTemplate(
    input_variables=["question", "tables"],
    template="""
You are a database schema selector. Your only job is to pick relevant table names.

User Question:
{question}

Available Tables:
{tables}

Rules:
- Return ONLY table names from the list above.
- If multiple, comma-separated.
- No explanation, no extra text.
"""
)


# SQL generation
sql_prompt = PromptTemplate(
    input_variables=["question", "schema", "examples"],
    template="""
You are an expert PostgreSQL data analyst. Your ONLY job is to write SQL queries.


IMPORTANT PostgreSQL RULE:
- PostgreSQL automatically lowercases unquoted identifiers.
- Any table OR column name that contains capital letters MUST be wrapped in double quotes.
- Always quote table names AND column names exactly as they appear in the schema.
- Never leave a capitalized identifier unquoted.

Here are similar example queries:

{examples}

Here is the database schema:
{schema}

Write a SQL query that answers:
{question}

STRICT RULES:
- Use ONLY table and column names from schema.
- Quote capitalized identifiers.
- Return ONLY the SQL query, nothing else.
"""
)


# Answer generation 
answer_prompt = PromptTemplate(
    input_variables=["question", "data", "is_limited"],
    template="""
User Question: {question}
SQL Data: {data}
Results were limited to 10 records: {is_limited}

Use the user question and the generated SQL data to provide a clear, readable, and well-structured answer.

If "Results were limited to 10 records" is True, add this note at the end:
"Note: The results shown are limited to 10 records as the query returned a large number of rows."

Do NOT share your opinion or add notes beyond what is asked. Write the answer in a readable and user-friendly form.
"""
)




# SQL fix
sql_fix_prompt = PromptTemplate(
    input_variables=["sql", "error", "schema"],
    template="""
You are a PostgreSQL expert. The following SQL query failed validation with this error:

Error: {error}

Broken SQL:
{sql}

Database schema for reference:
{schema}

Fix the SQL query so it is valid PostgreSQL. Return ONLY the corrected SQL query with no explanation or markdown.
"""
)



# Fallback suggestions
fallback_prompt = PromptTemplate(
    input_variables=["question", "schema"],
    template="""
You are a PostgreSQL expert. A user asked the following question but the system could not generate a working SQL query for it:

User Question: {question}

Database Schema:
{schema}

Your task:
1. Generate exactly 2 alternative questions that are very close in intent to the user's original question, but simpler or slightly rephrased so they are more likely to work with this schema.
2. For each alternative question, write a valid PostgreSQL query that answers it.
3. The queries MUST be valid PostgreSQL — they must run without errors against the schema above.
4. Quote all capitalized table and column names with double quotes.
5. Use ONLY tables and columns that exist in the schema.

Return your response in this EXACT format and nothing else:

SUGGESTION_1_QUESTION: <alternative question 1>
SUGGESTION_1_SQL: <valid sql query 1>
SUGGESTION_2_QUESTION: <alternative question 2>
SUGGESTION_2_SQL: <valid sql query 2>
"""
)
