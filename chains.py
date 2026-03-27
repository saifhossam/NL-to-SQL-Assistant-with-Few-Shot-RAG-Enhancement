from langchain_core.output_parsers import StrOutputParser
from config import get_llm
from prompts import sql_prompt, table_selector_prompt, answer_prompt, sql_fix_prompt



llm = get_llm()

sql_chain = sql_prompt | llm | StrOutputParser()
answer_chain = answer_prompt | llm | StrOutputParser()
table_selector_chain = table_selector_prompt | llm | StrOutputParser()
sql_fix_chain = sql_fix_prompt | llm | StrOutputParser()