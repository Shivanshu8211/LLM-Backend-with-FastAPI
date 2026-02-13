from app.background.worker import InMemoryJobStore, InMemoryJobWorker
from app.core.config import settings

job_store = InMemoryJobStore()
job_worker = InMemoryJobWorker(store=job_store, concurrency=settings.worker_concurrency)
