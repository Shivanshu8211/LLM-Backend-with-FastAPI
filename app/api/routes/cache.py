import statistics
import time

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.cache.state import get_cache
from app.core.metrics import route_latency_registry
from app.llm.inference import run_completion_sync

router = APIRouter()


class CacheBenchmarkRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    runs: int = Field(default=5, ge=2, le=50)
    warmup_runs: int = Field(default=1, ge=0, le=5)
    allow_semantic: bool = True


@router.get('/status')
async def cache_status():
    return get_cache().status()


@router.post('/invalidate')
async def cache_invalidate():
    started = time.perf_counter()
    removed = get_cache().clear()
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('cache.invalidate', elapsed)
    return {'removed_entries': removed, 'elapsed_seconds': round(elapsed, 4)}


@router.post('/benchmark')
async def cache_benchmark(payload: CacheBenchmarkRequest):
    started = time.perf_counter()
    cache = get_cache()

    # Keep benchmark runs bounded and repeatable.
    cache.clear()

    for _ in range(payload.warmup_runs):
        run_completion_sync(payload.prompt, use_cache=False)

    uncached_samples: list[float] = []
    for _ in range(payload.runs):
        t0 = time.perf_counter()
        run_completion_sync(payload.prompt, use_cache=False)
        uncached_samples.append(time.perf_counter() - t0)

    cache.clear()
    cached_samples: list[float] = []
    for _ in range(payload.runs):
        t0 = time.perf_counter()
        run_completion_sync(payload.prompt, use_cache=True, allow_semantic=payload.allow_semantic)
        cached_samples.append(time.perf_counter() - t0)

    elapsed = time.perf_counter() - started
    route_latency_registry.observe('cache.benchmark', elapsed)
    stats = cache.status().get('stats', {})

    uncached_avg = statistics.mean(uncached_samples) if uncached_samples else 0.0
    cached_avg = statistics.mean(cached_samples) if cached_samples else 0.0
    speedup = (uncached_avg / cached_avg) if cached_avg > 0 else 0.0

    return {
        'prompt': payload.prompt,
        'runs': payload.runs,
        'warmup_runs': payload.warmup_runs,
        'allow_semantic': payload.allow_semantic,
        'uncached': {
            'avg_seconds': round(uncached_avg, 4),
            'min_seconds': round(min(uncached_samples), 4),
            'max_seconds': round(max(uncached_samples), 4),
        },
        'cached': {
            'avg_seconds': round(cached_avg, 4),
            'min_seconds': round(min(cached_samples), 4),
            'max_seconds': round(max(cached_samples), 4),
        },
        'speedup_x': round(speedup, 3),
        'cache_stats': stats,
        'elapsed_seconds': round(elapsed, 4),
    }
