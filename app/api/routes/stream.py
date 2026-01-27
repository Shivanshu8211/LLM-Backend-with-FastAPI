# from fastapi import APIRouter
# from fastapi.responses import StreamingResponse
# from app.llm.streaming import stream_gemini_response

# router = APIRouter()

# print("This is your LLM")

# @router.get("/gemini")
# async def stream_llm(prompt: str):
#     async def event_generator():
#         try:
#             async for token in stream_gemini_response(prompt):
#                 yield f"data: {token}\n\n"
#         except Exception as e:
#             yield f"data: [ERROR] {str(e)}\n\n"

#     return StreamingResponse(
#         event_generator(),
#         media_type="text/event-stream"
#     )
import time
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.llm.streaming import stream_completion

router = APIRouter()


@router.get("/stream")
async def stream(prompt: str):
    start_time = time.time()

    async def event_generator():
        first_token_time = None

        async for token in stream_completion(prompt):
            if first_token_time is None:
                first_token_time = time.time()
                ttft = first_token_time - start_time
                yield f"event: metrics\ndata: TTFT={ttft:.3f}s\n\n"

            yield f"data: {token}\n\n"

        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
