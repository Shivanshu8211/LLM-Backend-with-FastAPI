import asyncio
from typing import AsyncGenerator

from app.llm.gemini_client import stream_gemini_completion_sync


async def stream_completion(prompt: str) -> AsyncGenerator[str, None]:
    """
    Async wrapper around sync Gemini streaming.
    """
    loop = asyncio.get_running_loop()

    for token in stream_gemini_completion_sync(prompt):
        # Yield control back to event loop between tokens
        await asyncio.sleep(0)
        yield token

