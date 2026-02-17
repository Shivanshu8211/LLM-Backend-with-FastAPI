import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.chains.state import get_orchestrator
from app.core.config import settings
from app.core.metrics import route_latency_registry

router = APIRouter()


class ChainAskRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    top_k: int = Field(default=settings.rag_default_top_k, ge=1, le=20)
    use_rag: bool = True
    use_tools: bool = True


@router.get("/status")
async def chain_status():
    orchestrator = get_orchestrator()
    return {
        "chain_mode": settings.chain_mode,
        "tools": orchestrator.tool_names,
        "tool_max_invocations_per_request": settings.tool_max_invocations_per_request,
    }


@router.post("/ask-sync")
def chain_ask_sync(payload: ChainAskRequest):
    started = time.perf_counter()
    orchestrator = get_orchestrator()
    result = orchestrator.run_sync(
        prompt=payload.prompt,
        top_k=payload.top_k,
        use_rag=payload.use_rag,
        use_tools=payload.use_tools,
    )
    elapsed = time.perf_counter() - started
    route_latency_registry.observe("chains.ask_sync", elapsed)
    result["elapsed_seconds"] = round(elapsed, 3)
    return result


@router.post("/ask-async")
async def chain_ask_async(payload: ChainAskRequest):
    started = time.perf_counter()
    orchestrator = get_orchestrator()
    result = await orchestrator.run_async(
        prompt=payload.prompt,
        top_k=payload.top_k,
        use_rag=payload.use_rag,
        use_tools=payload.use_tools,
    )
    elapsed = time.perf_counter() - started
    route_latency_registry.observe("chains.ask_async", elapsed)
    result["elapsed_seconds"] = round(elapsed, 3)
    return result


@router.get("/tools/logs")
async def chain_tool_logs(limit: int = 50):
    orchestrator = get_orchestrator()
    return {"logs": orchestrator.get_logs(limit=limit)}
