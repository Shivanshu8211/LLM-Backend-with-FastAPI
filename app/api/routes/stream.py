from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.llm.streaming import stream_gemini_response

router = APIRouter()

print("This is your LLM")

@router.get("/gemini")
async def stream_llm(prompt: str):
    async def event_generator():
        try:
            async for token in stream_gemini_response(prompt):
                yield f"data: {token}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
