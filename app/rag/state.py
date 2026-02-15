from __future__ import annotations

import threading

from app.core.config import settings
from app.rag.embeddings import build_embedding_model
from app.rag.ingestion import build_chunks
from app.rag.retriever import IndexStats, RagRetriever
from app.rag.vector_store import JsonVectorStore

_retriever_lock = threading.Lock()
_retriever: RagRetriever | None = None


def get_retriever() -> RagRetriever:
    global _retriever
    with _retriever_lock:
        if _retriever is None:
            embedding_model = build_embedding_model()
            vector_store = JsonVectorStore(settings.vector_store_path)
            _retriever = RagRetriever(embedding_model=embedding_model, vector_store=vector_store)
        return _retriever


def index_documents(rebuild: bool = False) -> IndexStats:
    retriever = get_retriever()
    chunks = build_chunks()
    payload = [
        {
            'chunk_id': chunk.chunk_id,
            'text': chunk.text,
            'metadata': chunk.metadata,
        }
        for chunk in chunks
    ]
    return retriever.index_chunks(payload, rebuild=rebuild)
