import asyncio
from text2sql.pipeline.keyword_extractor import extract_keywords
from text2sql.pipeline.entity_retriever import entity_retrieval
from text2sql.pipeline.table_selector import select_tables
from text2sql.pipeline.column_selector import select_columns
from text2sql.pipeline.query_generator import generate_sql_query
from text2sql.pipeline.query_executer import execute_and_fix_query

from text2sql.utils.schema_loader import load_schema
from langchain_openai import AzureChatOpenAI

# ----------------------------------------
# CONFIG
# ----------------------------------------

AZURE_ENDPOINT = "<input endpoint>"
AZURE_API_KEY = "<input key>"
MODEL = "gpt-4o-mini"

DB_CONNECTION_STRING = "postgresql://user:pass@localhost:5432/mydb"
SCHEMA_FILE = "schema.json"  # your preprocessed schema

# ----------------------------------------
# Local Runner
# ----------------------------------------

async def run_text2sql(user_query: str):

    print("\n Loading LLM")
    llm = AzureChatOpenAI(
        azure_deployment=MODEL,
        api_key=AZURE_API_KEY,
        azure_endpoint=AZURE_ENDPOINT,
        temperature=0
    )

    print(" Loading schema...")
    schema = load_schema(SCHEMA_FILE)

    print("\n Extracting keywords...")
    keywords = await extract_keywords(llm, user_query)
    print("   ➤", keywords)

    print("\n Retrieving entities...")
    entities = await entity_retrieval(user_query, schema)
    print("   ➤", entities)

    print("\n Selecting tables...")
    tables = await select_tables(llm, user_query, schema, keywords, entities)
    print("   ➤", tables)

    print("\n Selecting columns...")
    columns = await select_columns(llm, user_query, schema, tables)
    print("   ➤", columns)

    print("\n Generating SQL...")
    sql = await generate_sql_query(llm, user_query, schema, tables, columns)
    print("   ➤", sql)

    print("\n Executing SQL...")
    df = execute_and_fix_query(DB_CONNECTION_STRING, sql)
    print(df)

    return {
        "sql": sql,
        "data": df.to_dict(orient="records")
    }

# ----------------------------------------
# Run the agent
# ----------------------------------------

if __name__ == "__main__":
    q = input("Enter your question: ")
    asyncio.run(run_text2sql(q))
