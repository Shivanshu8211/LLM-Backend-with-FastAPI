from fastapi import APIRouter, BackgroundTasks
from app.background.tasks import create_job, long_running_task, JOB_RESULTS
from datetime import datetime

router = APIRouter()

@router.post("/submit")
async def submit_job(background_tasks: BackgroundTasks):
    job_id = create_job()
    background_tasks.add_task(long_running_task, job_id)

    return {
        "job_id": job_id,
        "status": "accepted"
    }

@router.get("/{job_id}")
async def get_job_status(job_id: str):
    return JOB_RESULTS.get(job_id, {"status": "unknown job"})
