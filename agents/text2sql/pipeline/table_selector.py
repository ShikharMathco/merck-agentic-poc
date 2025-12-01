from fastapi.logger import logger
from agents.text2sql.pipeline.util import extract_json
from agents.text2sql.prompts.table_selection_prompt import table_selection_prompt 

async def select_tables(llm: AzureChatOpenAI, user_query: str, database_schema: str, kpi_doc: str) -> tuple[list, int, int]:
    try:
        PROMPT = table_selection_prompt.format(user_query=user_query, database_schema=database_schema, kpi_doc=kpi_doc)
        response = await llm.ainvoke(PROMPT)
        response_json = extract_json(response.content)
        tables = response_json.get("tables", [])
        return (
            tables, 
            response.usage_metadata.get("input_tokens", 0), 
            response.usage_metadata.get("output_tokens", 0)
        )
    except Exception as e:
        logger.error(f"Error Selecting Tables: {e}", exc_info=True)
        return ([], 0, 0)
