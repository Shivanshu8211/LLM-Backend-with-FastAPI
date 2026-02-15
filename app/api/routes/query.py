import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.metrics import route_latency_registry
from app.llm.inference import run_completion, run_completion_sync
from app.rag.pipeline import rag_answer_async, rag_answer_sync
from app.rag.state import get_retriever

router = APIRouter()


class QueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


class RagQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    top_k: int = Field(default=settings.rag_default_top_k, ge=1, le=20)


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


@router.post('/rag-sync')
def query_rag_sync(payload: RagQueryRequest):
    started = time.perf_counter()
    retriever = get_retriever()
    answer = rag_answer_sync(retriever=retriever, prompt=payload.prompt, top_k=payload.top_k)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('query.rag_sync', elapsed)
    answer['mode'] = 'rag-sync'
    answer['elapsed_seconds'] = round(elapsed, 3)
    return answer


@router.post('/rag-async')
async def query_rag_async(payload: RagQueryRequest):
    started = time.perf_counter()
    retriever = get_retriever()
    answer = await rag_answer_async(retriever=retriever, prompt=payload.prompt, top_k=payload.top_k)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('query.rag_async', elapsed)
    answer['mode'] = 'rag-async'
    answer['elapsed_seconds'] = round(elapsed, 3)
    return answer
