from agents.text2sql.pipeline.util import extract_json
from fastapi.logger import logger
from langchain_openai import AzureChatOpenAI
from agents.text2sql.prompts.column_selection_prompt import column_selection_prompt

async def select_columns(
    llm: AzureChatOpenAI,
    user_query: str,
    database_schema: str,
    kpi_doc: str
) -> tuple[dict, int, int]:
    try:
        PROMPT = column_selection_prompt.format(
            user_query=user_query,
            database_schema=database_schema,
            kpi_doc=kpi_doc
        )
        response = await llm.ainvoke(PROMPT)
        return (
            extract_json(response.content), 
            response.usage_metadata.get("input_tokens", 0), 
            response.usage_metadata.get("output_tokens", 0)
        )
    except Exception as e:
        logger.error(f"Error selecting column: {e}")
        return ({}, 0, 0)
