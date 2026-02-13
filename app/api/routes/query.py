import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.metrics import route_latency_registry
from app.llm.inference import run_completion, run_completion_sync

router = APIRouter()


class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


@router.post('/sync')
def query_sync(payload: QueryRequest):
    started = time.perf_counter()
    output = run_completion_sync(payload.prompt)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('query.sync', elapsed)
    return {'mode': 'sync', 'output': output, 'elapsed_seconds': round(elapsed, 3)}


@router.post('/async')
async def query_async(payload: QueryRequest):
    started = time.perf_counter()
    output = await run_completion(payload.prompt)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('query.async', elapsed)
    return {'mode': 'async', 'output': output, 'elapsed_seconds': round(elapsed, 3)}
