from fastapi import APIRouter

from app.background.tasks import job_store, job_worker

router = APIRouter()


@router.get('/')
async def health_check():
    stats = await job_store.stats()
    return {
        'status': 'ok',
        'service': 'llm-backend',
        'mode': 'async',
        'worker_running': job_worker.is_running,
        'queue_size': job_worker.queue_size,
        'job_stats': stats,
    }
