from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import chains, demo, health, jobs, query, rag, stream, ui
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


app = FastAPI(title=f"{settings.app_name} - Phase 6", lifespan=lifespan)

frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount("/ui", StaticFiles(directory=str(frontend_dir)), name="ui-static")

app.include_router(ui.router)
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(demo.router, prefix="/demo", tags=["demo"])
app.include_router(query.router, prefix="/query", tags=["query"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(stream.router, prefix="/stream", tags=["stream"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(chains.router, prefix="/chains", tags=["chains"])
