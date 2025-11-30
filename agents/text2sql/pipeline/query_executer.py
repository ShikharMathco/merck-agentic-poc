import logging
from langchain_openai import AzureChatOpenAI
import pandas as pd
from sqlalchemy import create_engine, text
from agents.text2sql.pipeline.util import extract_json
from agents.text2sql.prompts.query_revision_prompt import query_revision_prompt

async def execute_and_fix_query(
    llm: AzureChatOpenAI, 
    connection_string: str,
    schema_name: str,
    sql_query: str,
    user_query: str, 
    dialect: str,
    database_schema: str,
    context_info: str,
    app_context: str = "",
    max_retries: int = 3
):
    total_input_token_used = 0
    total_output_token_used = 0
    initial_sql_query = sql_query
    error_message = ""
    revised_sql_query = None
    data = pd.DataFrame()
    db_engine = None
    try:
        db_engine = create_engine(connection_string, connect_args={"options": f"-csearch_path={schema_name}"})
        for _ in range(max_retries):
            with db_engine.connect() as connection:
                try:
                    data = pd.read_sql(con=connection, sql=text(sql_query))
                    data = data.fillna(0).round(2)
                    error_message = ""
                except Exception as run_error:
                    error_message = str(run_error)
                    data = pd.DataFrame()
            if error_message:
                PROMPT = query_revision_prompt.format(
                    database_schema = database_schema,
                    user_query = user_query,
                    kpi_docs = str(app_context)+str(context_info),
                    query = sql_query,
                    dialect = dialect,
                    error_message = error_message
                )
                response = await llm.ainvoke(PROMPT)
                fixed_query_response = extract_json(response.content)
                sql_query = fixed_query_response.get("SQL", fixed_query_response.get("sql", sql_query))
                if "```sql" in sql_query:
                    sql_query = sql_query.replace("```sql", "").replace("```", "")
                sql_query = sql_query.replace("\n", " ").replace("\\", "").replace("%","%%").strip()
                revised_sql_query = sql_query
                total_input_token_used += response.usage_metadata.get("input_tokens", 0)
                total_output_token_used += response.usage_metadata.get("output_tokens", 0)
            else:
                break
    except Exception as e:
        logging.info(f"Error Running and Fixing SQL Query: {e}", exc_info=True)
    finally:
        if db_engine:
            db_engine.dispose()
        # return {
        #     "initial_sql_query": initial_sql_query,
        #     "revised_sql_query": revised_sql_query or initial_sql_query,
        #     "error": error_message if error_message else None,
        #     "input_tokens": total_input_token_used,
        #     "output_tokens": total_output_token_used,
        #     "dataframe": data
        # }
        final_query = revised_sql_query or initial_sql_query
    return(
        sql_query,
        error_message,
        total_input_token_used,
        total_output_token_used,
        data
    )
