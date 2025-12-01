import asyncio
from text2sql.pipeline.keyword_extractor import extract_keywords
from text2sql.pipeline.table_selector import select_tables
from text2sql.pipeline.column_selector import select_columns
from text2sql.pipeline.query_generator import generate_sql_query_gptel
from text2sql.pipeline.query_executer import execute_and_fix_query
from text2sql.pipeline.entity_retriever import get_context_documents
from text2sql.utils.schema_loader import load_schema
from text2sql.llm_gptel import GPTELChatLLM  # custom GPTEL wrapper

# ----------------------------------------
# CONFIG
# ----------------------------------------

GPTEL_KEY = "<your company key>"
GPTEL_ENDPOINT = "<your company endpoint>"

DB_CONNECTION_STRING = "postgresql://your_user:your_pass@localhost:5432/dummy_poc"
SCHEMA_FILE = "schema.json"
CONTEXT_FOLDER = "context_input"  # folder containing your context documents
DB_DIALECT = "postgresql"         # adjust if using MySQL, etc.

# ----------------------------------------
# Local Runner
# ----------------------------------------

async def run_text2sql(user_query: str):

    # print("\n Loading GPTEL LLM...")
    # llm = GPTELChatLLM(
    #     api_key=GPTEL_KEY,
    #     endpoint=GPTEL_ENDPOINT,
    #     temperature=0.2
    # )

    # print(" Loading schema...")
    # schema = load_schema(SCHEMA_FILE)

    # print("\n Extracting keywords...")
    # keywords = await extract_keywords(llm, user_query)
    # print("   ➤", keywords)

    print("\n Loading context documents...")
    context_docs = get_context_documents(CONTEXT_FOLDER)
    full_context = "\n\n".join(context_docs)
    print("   ➤ Loaded", len(context_docs), "documents.")

    print("\n Selecting tables...")
    tables = await select_tables(llm, user_query, schema, keywords, full_context)
    print("   ➤", tables)

    print("\n Selecting columns...")
    columns = await select_columns(llm, user_query, schema, tables)
    print("   ➤", columns)

    print("\n Generating SQL...")
    sql, input_tokens, output_tokens = await generate_sql_query_gptel(
        gptel=llm,
        user_query=user_query,
        dialect=DB_DIALECT,
        database_schema=schema,
        context_info=full_context
    )
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
