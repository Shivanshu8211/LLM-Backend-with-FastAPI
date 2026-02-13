from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import demo, health, jobs, query, stream
from app.background.tasks import job_worker
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await job_worker.start()
    try:
        yield
    finally:
        await job_worker.stop()


app = FastAPI(title=f'{settings.app_name} - Phase 4', lifespan=lifespan)

app.include_router(health.router, prefix='/health', tags=['health'])
app.include_router(demo.router, prefix='/demo', tags=['demo'])
app.include_router(query.router, prefix='/query', tags=['query'])
app.include_router(jobs.router, prefix='/jobs', tags=['jobs'])
app.include_router(stream.router, prefix='/stream', tags=['stream'])
