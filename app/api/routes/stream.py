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
async def stream_response(request: Request, prompt: str):
    """
    Server-Sent Events streaming endpoint.
    """

    async def event_generator():
        start_time = time.perf_counter()
        first_token_time = None

        try:
            async for token in stream_completion(prompt):

                # Handle client disconnect
                if await request.is_disconnected():
                    print("Client disconnected")
                    break

                if first_token_time is None:
                    first_token_time = time.perf_counter()
                    ttft = first_token_time - start_time
                    print(f"[METRIC] TTFT: {ttft:.3f}s")

                yield f"data: {token}\n\n"

                # Yield control to event loop
                await asyncio.sleep(0)

        finally:
            total_time = time.perf_counter() - start_time
            print(f"[METRIC] Total Stream Time: {total_time:.3f}s")

            yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
