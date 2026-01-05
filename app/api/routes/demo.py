import time
import asyncio
from fastapi import APIRouter

router = APIRouter()

# ❌ Blocking (Sync-style)
@router.get("/sync")
def sync_endpoint():
    time.sleep(5)   # blocks worker thread
    return {"type": "sync", "message": "Completed after 5 seconds"}

# ✅ Non-blocking Async
@router.get("/async")
async def async_endpoint():
    await asyncio.sleep(5)  # releases event loop
    return {"type": "async", "message": "Completed after 5 seconds"}
