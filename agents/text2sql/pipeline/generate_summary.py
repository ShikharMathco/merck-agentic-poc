from typing import AsyncGenerator
from fastapi.logger import logger
from text2sql.llm_gptel import GPTELChatLLM  # your company LLM wrapper
from text2sql.prompts.generate_summary_prompt import generate_summary_prompt
 
async def generate_summary(
    llm: GPTELChatLLM,
    user_query: str,
    dataframe: str,
    bus_context: str
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields summary/insight chunks produced by GPTEL.

    Args:
        llm: instance of GPTELChatLLM
        user_query: original question
        dataframe: markdown representation of dataframe or special cases "empty"/"large"
        bus_context: business context

    Yields:
        str: streamed or full summary text
    """
    try:
        # special case: no data found
        if dataframe == "empty":
            yield (
                "Sorry, but I couldn't find any data based on your query. "
                "It's possible that the query parameters need adjustment. "
                "Please double-check or try a different query."
            )
            return

        # special case: large dataset
        if dataframe == "large":
            yield "What else would you like to know?"
            return

        # build prompt
        prompt = generate_summary_prompt.format(
            user_query=user_query,
            dataframe=dataframe,
            bus_context=bus_context
        )

        # prefer streaming if available
        if hasattr(llm, "stream") and callable(getattr(llm, "stream")):
            async for chunk in llm.stream(prompt):
                content = None
                if isinstance(chunk, str):
                    content = chunk
                else:
                    content = getattr(chunk, "content", None) or getattr(chunk, "text", None)

                if content:
                    yield content
            return

        # fallback: non-streaming
        if hasattr(llm, "ainvoke") and callable(getattr(llm, "ainvoke")):
            response = await llm.ainvoke(prompt)

            if isinstance(response, str):
                yield response
                return

            content = getattr(response, "content", None) or getattr(response, "text", None)
            if content:
                yield content
                return

        # unexpected format
        logger.error("LLM did not provide a response in expected format.")
        yield "Sorry, I couldn't generate a summary at this time."

    except Exception as e:
        logger.error("Error generating summary: %s", e, exc_info=True)
        yield "What else would you like to know?"
