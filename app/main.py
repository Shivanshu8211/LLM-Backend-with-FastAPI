from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import demo, health, jobs, query, rag, stream
from app.background.tasks import job_worker
from app.core.config import settings
from app.core.logging import setup_logging
from app.rag.state import index_documents

setup_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await job_worker.start()

    # Phase 5: Best-effort warm index build for RAG startup convenience.
    try:
        index_documents(rebuild=False)
    except Exception:
        pass

    try:
        yield
    finally:
        await job_worker.stop()


app = FastAPI(title=f'{settings.app_name} - Phase 5', lifespan=lifespan)

app.include_router(health.router, prefix='/health', tags=['health'])
app.include_router(demo.router, prefix='/demo', tags=['demo'])
app.include_router(query.router, prefix='/query', tags=['query'])
app.include_router(jobs.router, prefix='/jobs', tags=['jobs'])
app.include_router(stream.router, prefix='/stream', tags=['stream'])
app.include_router(rag.router, prefix='/rag', tags=['rag'])
