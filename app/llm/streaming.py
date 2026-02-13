from typing import AsyncGenerator
import threading

from app.llm.inference import stream_completion as stream_completion_core


async def stream_completion(prompt: str, cancel_event: threading.Event | None = None) -> AsyncGenerator[str, None]:
    async for token in stream_completion_core(prompt, cancel_event=cancel_event):
        yield token
