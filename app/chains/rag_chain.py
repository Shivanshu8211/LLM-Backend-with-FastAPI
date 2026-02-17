from __future__ import annotations

from app.core.config import settings
from app.rag.state import get_retriever


def retrieve_context(query: str, top_k: int | None = None, max_chars: int | None = None) -> tuple[str, list[dict]]:
    retriever = get_retriever()
    context, results = retriever.build_context(
        query=query,
        top_k=top_k or settings.rag_default_top_k,
        max_chars=max_chars or settings.chain_max_context_chars,
    )

    retrieved = [
        {
            "score": round(item.score, 4),
            "source_path": item.metadata.get("source_path"),
            "chunk_index": item.metadata.get("chunk_index"),
            "text": item.text,
        }
        for item in results
    ]
    return context, retrieved
