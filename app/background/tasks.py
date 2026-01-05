import asyncio
import uuid
from datetime import datetime

# In-memory job store (Phase 3 only)
JOB_RESULTS = {}

async def long_running_task(job_id: str):
    # Simulate LLM inference
    await asyncio.sleep(10)

    JOB_RESULTS[job_id] = {
        "status": "completed",
        "result": f"LLM output for job {job_id}",
        "completed at time-stamp": datetime.now().strftime("%H:%M:%S")
    }

def create_job():
    job_id = str(uuid.uuid4())
    JOB_RESULTS[job_id] = {"status": "processing"}
    return job_id
