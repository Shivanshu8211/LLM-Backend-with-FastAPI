# import asyncio
# from app.llm.gemini_client import get_gemini_client

# async def stream_gemini_response(prompt: str):
#     client = get_gemini_client()

#     response = client.models.generate_content_stream(
#         model="gemini-2.5-flash",
#         contents=prompt
#     )

#     for chunk in response:
#         if chunk.text:
#             # Yield token/chunk to FastAPI
#             yield chunk.text

#         # Allow event loop to breathe
#         await asyncio.sleep(0)
import time
from typing import AsyncGenerator

from app.llm.gemini_client import stream_gemini_completion


async def stream_completion(prompt: str) -> AsyncGenerator[str, None]:
    """
    Provider-agnostic streaming interface.
    """
    # Currently Gemini is the active provider
    async for token in stream_gemini_completion(prompt):
        yield token
