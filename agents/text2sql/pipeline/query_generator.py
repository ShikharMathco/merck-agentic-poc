from fastapi.logger import logger
from text2sql.pipeline.util import extract_json
from langchain_openai import AzureChatOpenAI
from text2sql.prompts.generate_sql_prompt import sql_generation_prompt
async def generate_sql_query(
    llm: AzureChatOpenAI,
    user_query: str,
    dialect: str,
    database_schema: str,
    context_info: str,
    app_context: str = "",
    num_candidates: int = 1
) -> tuple[str, int, int]:
    try:
        PROMPT = sql_generation_prompt.format(
            dialect=dialect,
            database_schema=database_schema,
            user_query=user_query,
            app_context=f"Important Information (to be considered irrespective on the user question):\n{app_context}" if app_context else "",
            kpi_docs=context_info,
        )
        response = await llm.ainvoke(PROMPT)
        response_json = extract_json(response.content)
        sql_query = response_json.get("SQL", response_json.get("sql", response_json.get("sql_query", "")))
        if "```sql" in sql_query:
            sql_query = sql_query.replace("```sql", "").replace("```", "")
        sql_query = sql_query.replace("\n", " ").replace("\\", "").replace("%","%%").strip()
        return (
            sql_query, 
            response.usage_metadata.get("input_tokens", 0), 
            response.usage_metadata.get("output_tokens", 0)
        )
    except Exception as e:
        logger.info(f"Error Generating SQL Candidates: {e}")
        return ("", 0, 0)
