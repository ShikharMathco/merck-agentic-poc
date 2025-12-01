from fastapi.logger import logger
from agents.text2sql.pipeline.util import extract_list
from agents.text2sql.prompts.keyword_extraction_prompt import keyword_extraction_prompt

async def extract_keywords(llm: AzureChatOpenAI, user_query: str, kpi_doc: str = ""):
    try:
        PROMPT = keyword_extraction_prompt.format(user_query=user_query, kpi_doc=kpi_doc)
        response = await llm.ainvoke(PROMPT)
        extracted_keywords = extract_list(response.content)
        if extracted_keywords:
            return (
                extracted_keywords,
                response.usage_metadata.get("input_tokens", 0),
                response.usage_metadata.get("output_tokens", 0)
            )
        else:
            raise
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}", exc_info=True)
        return (user_query.split(), 0, 0)
