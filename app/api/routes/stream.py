import threading

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.metrics import StreamMetrics
from app.llm.streaming import stream_completion

router = APIRouter()


@router.get('/stream')
async def stream(prompt: str, request: Request):
    metrics = StreamMetrics()
    cancel_event = threading.Event()

    async def event_generator():
        try:
            async for token in stream_completion(prompt, cancel_event=cancel_event):
                if await request.is_disconnected():
                    cancel_event.set()
                    break

                if metrics.first_token_at is None:
                    metrics.mark_first_token()
                    ttft = metrics.ttft_seconds or 0.0
                    yield f'event: metrics\ndata: {{"ttft_seconds": {ttft:.3f}}}\n\n'

                yield f'data: {token}\n\n'

            if not await request.is_disconnected():
                total = metrics.total_seconds
                yield f'event: metrics\ndata: {{"total_seconds": {total:.3f}}}\n\n'
                yield 'event: done\ndata: [DONE]\n\n'
        finally:
            cancel_event.set()

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )
