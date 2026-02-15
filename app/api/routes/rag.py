import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.metrics import route_latency_registry
from app.rag.evaluation import RetrievalEvalCase, evaluate_retrieval
from app.rag.ingestion import build_chunks
from app.rag.pipeline import rag_answer_async, rag_answer_sync
from app.rag.state import get_retriever, index_documents

router = APIRouter()


class IndexRequest(BaseModel):
    rebuild: bool = True


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=settings.rag_default_top_k, ge=1, le=20)


class AskRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    top_k: int = Field(default=settings.rag_default_top_k, ge=1, le=20)


class EvalCaseRequest(BaseModel):
    query: str = Field(..., min_length=1)
    expected_terms: list[str] = Field(default_factory=list)


class EvalRequest(BaseModel):
    top_k: int = Field(default=settings.rag_default_top_k, ge=1, le=20)
    cases: list[EvalCaseRequest]


@router.get('/status')
async def rag_status():
    retriever = get_retriever()
    return {
        'embedding_model': retriever.embedding_model_name,
        'indexed_chunks': retriever.index_size,
    }


@router.post('/index')
async def rag_index(payload: IndexRequest):
    started = time.perf_counter()
    stats = index_documents(rebuild=payload.rebuild)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('rag.index', elapsed)

    return {
        'indexed_chunks': stats.indexed_chunks,
        'embedding_model': stats.embedding_model,
        'embedding_dimension': stats.embedding_dimension,
        'elapsed_seconds': round(elapsed, 3),
    }


@router.post('/search')
async def rag_search(payload: SearchRequest):
    started = time.perf_counter()
    retriever = get_retriever()
    results = retriever.retrieve(payload.query, top_k=payload.top_k)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('rag.search', elapsed)

    return {
        'query': payload.query,
        'top_k': payload.top_k,
        'results': [
            {
                'score': round(item.score, 4),
                'source_path': item.metadata.get('source_path'),
                'chunk_index': item.metadata.get('chunk_index'),
                'text': item.text,
            }
            for item in results
        ],
        'elapsed_seconds': round(elapsed, 4),
    }


@router.post('/ask-sync')
def rag_ask_sync(payload: AskRequest):
    started = time.perf_counter()
    retriever = get_retriever()
    answer = rag_answer_sync(retriever=retriever, prompt=payload.prompt, top_k=payload.top_k)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('rag.ask_sync', elapsed)
    answer['elapsed_seconds'] = round(elapsed, 3)
    return answer


@router.post('/ask-async')
async def rag_ask_async(payload: AskRequest):
    started = time.perf_counter()
    retriever = get_retriever()
    answer = await rag_answer_async(retriever=retriever, prompt=payload.prompt, top_k=payload.top_k)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('rag.ask_async', elapsed)
    answer['elapsed_seconds'] = round(elapsed, 3)
    return answer


@router.post('/analyze')
async def rag_analyze(payload: EvalRequest):
    retriever = get_retriever()
    cases = [RetrievalEvalCase(query=item.query, expected_terms=item.expected_terms) for item in payload.cases]
    report = evaluate_retrieval(retriever=retriever, cases=cases, top_k=payload.top_k)
    report['top_k'] = payload.top_k
    report['indexed_chunks'] = retriever.index_size
    return report


@router.get('/sources')
async def rag_sources_preview():
    chunks = build_chunks()
    return {
        'files_detected': len({chunk.metadata.get('source_path') for chunk in chunks}),
        'chunks_if_indexed': len(chunks),
    }
