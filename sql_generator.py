from chains import sql_chain, sql_fix_chain
from rag.retriever import retrieve_examples


def get_sql(question, schema, examples=None):

    examples = retrieve_examples(question)

    sql = sql_chain.invoke({
        "question": question,
        "schema": schema,
        "examples": examples or "No examples provided."
    })

    return sql.replace("```sql", "").replace("```", "").strip()



def fix_sql(sql_query, error_message, schema):

    sql = sql_fix_chain.invoke({
        "sql": sql_query,
        "error": error_message,
        "schema": schema
    })

    return sql.replace("```sql", "").replace("```", "").strip()