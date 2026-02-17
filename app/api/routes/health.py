from fastapi import APIRouter

from app.background.tasks import job_store, job_worker
from app.chains.state import get_orchestrator
from app.core.config import settings
from app.rag.state import get_retriever

router = APIRouter()


@router.get('/')
async def health_check():
    stats = await job_store.stats()
    rag = get_retriever()
    chains = get_orchestrator()
    return {
        'status': 'ok',
        'service': 'llm-backend',
        'mode': 'async',
        'worker_running': job_worker.is_running,
        'queue_size': job_worker.queue_size,
        'job_stats': stats,
        'rag': {
            'embedding_model': rag.embedding_model_name,
            'indexed_chunks': rag.index_size,
        },
        'chains': {
            'chain_mode': settings.chain_mode,
            'tools': chains.tool_names,
        },
    }
