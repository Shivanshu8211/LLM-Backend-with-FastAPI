from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.background.tasks import job_store, job_worker

router = APIRouter()


class SubmitJobRequest(BaseModel):
    prompt: str = Field(..., min_length=1)


@router.post('/submit')
async def submit_job(payload: SubmitJobRequest):
    job = await job_worker.submit(prompt=payload.prompt)
    return {'job_id': job.id, 'status': job.status}


@router.get('/{job_id}')
async def get_job_status(job_id: str):
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')

    return {
        'job_id': job.id,
        'status': job.status,
        'created_at': job.created_at,
        'started_at': job.started_at,
        'completed_at': job.completed_at,
        'result': job.result,
        'error': job.error,
    }
