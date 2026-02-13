from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.llm.inference import run_completion

JobStatus = Literal['queued', 'running', 'completed', 'failed']


@dataclass
class JobRecord:
    id: str
    prompt: str
    status: JobStatus
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: str | None = None
    error: str | None = None


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def create(self, prompt: str) -> JobRecord:
        job = JobRecord(id=str(uuid.uuid4()), prompt=prompt, status='queued')
        async with self._lock:
            self._jobs[job.id] = job
        return job

    async def get(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def set_running(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs[job_id]
            job.status = 'running'
            job.started_at = time.time()

    async def set_completed(self, job_id: str, result: str) -> None:
        async with self._lock:
            job = self._jobs[job_id]
            job.status = 'completed'
            job.completed_at = time.time()
            job.result = result

    async def set_failed(self, job_id: str, error: str) -> None:
        async with self._lock:
            job = self._jobs[job_id]
            job.status = 'failed'
            job.completed_at = time.time()
            job.error = error

    async def stats(self) -> dict[str, int]:
        async with self._lock:
            counts = {'queued': 0, 'running': 0, 'completed': 0, 'failed': 0}
            for job in self._jobs.values():
                counts[job.status] += 1
            return counts


class InMemoryJobWorker:
    def __init__(self, store: InMemoryJobStore, concurrency: int = 4) -> None:
        self._store = store
        self._concurrency = max(1, concurrency)
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for _ in range(self._concurrency):
            self._workers.append(asyncio.create_task(self._worker_loop()))

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        for _ in self._workers:
            await self._queue.put('__shutdown__')
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit(self, prompt: str) -> JobRecord:
        job = await self._store.create(prompt=prompt)
        await self._queue.put(job.id)
        return job

    async def _worker_loop(self) -> None:
        while True:
            job_id = await self._queue.get()
            if job_id == '__shutdown__':
                break

            job = await self._store.get(job_id)
            if not job:
                continue

            await self._store.set_running(job_id)
            try:
                result = await run_completion(job.prompt)
                await self._store.set_completed(job_id, result)
            except Exception as exc:
                await self._store.set_failed(job_id, str(exc))
