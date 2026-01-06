from fastapi import FastAPI
from app.core.logging import setup_logging
from app.api.routes import health, demo, jobs, stream

setup_logging()

app = FastAPI(title="LLM Backend - Phase 2")

app.include_router(testpage.router, prefix="/testpage")
app.include_router(health.router, prefix="/health")
app.include_router(demo.router, prefix="/demo")
app.include_router(jobs.router, prefix="/jobs")
app.include_router(stream.router, prefix="/stream")