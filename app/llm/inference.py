from __future__ import annotations

import asyncio
import threading
from typing import AsyncGenerator

from app.cache.state import get_cache
from app.llm.gemini_client import build_llm_provider
from app.llm.provider import BaseLLMProvider


_provider: BaseLLMProvider | None = None
_provider_lock = threading.Lock()


def get_provider() -> BaseLLMProvider:
    global _provider
    with _provider_lock:
        if _provider is None:
            _provider = build_llm_provider()
        return _provider


def run_completion_sync(prompt: str, use_cache: bool = True, allow_semantic: bool = True) -> str:
    if use_cache:
        cache = get_cache()
        hit = cache.lookup(prompt=prompt, allow_semantic=allow_semantic)
        if hit.hit and hit.output is not None:
            return hit.output

    output = get_provider().complete(prompt)
    if use_cache:
        get_cache().store(prompt=prompt, output=output)
    return output


async def run_completion(prompt: str, use_cache: bool = True, allow_semantic: bool = True) -> str:
    return await asyncio.to_thread(run_completion_sync, prompt, use_cache, allow_semantic)


async def stream_completion(prompt: str, cancel_event: threading.Event | None = None) -> AsyncGenerator[str, None]:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def producer() -> None:
        try:
            for token in get_provider().stream(prompt):
                if cancel_event and cancel_event.is_set():
                    break
                loop.call_soon_threadsafe(queue.put_nowait, token)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    producer_task = asyncio.to_thread(producer)
    background_task = asyncio.create_task(producer_task)

    try:
        while True:
            token = await queue.get()
            if token is None:
                break
            yield token
    finally:
        if cancel_event:
            cancel_event.set()
        await background_task
