import asyncio
import time

from fastapi import APIRouter

from app.core.metrics import route_latency_registry

router = APIRouter()


@router.get('/sync')
def sync_endpoint():
    started = time.perf_counter()
    time.sleep(5)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('demo.sync', elapsed)
    return {'type': 'sync', 'message': 'Completed after 5 seconds', 'elapsed_seconds': round(elapsed, 3)}


@router.get('/async')
async def async_endpoint():
    started = time.perf_counter()
    await asyncio.sleep(5)
    elapsed = time.perf_counter() - started
    route_latency_registry.observe('demo.async', elapsed)
    return {'type': 'async', 'message': 'Completed after 5 seconds', 'elapsed_seconds': round(elapsed, 3)}


@router.get('/metrics')
async def demo_metrics():
    return route_latency_registry.snapshot()
