from __future__ import annotations

from dataclasses import dataclass

from app.rag.state import get_retriever


@dataclass
class LookupResult:
    key: str
    found: bool
    value: str | None = None


# Simple in-memory key-value lookup to represent "database lookup" in Phase 6.
LOOKUP_DB = {
    "project": "High-Performance LLM Backend with FastAPI, RAG, and tool calling.",
    "framework": "FastAPI",
    "vector_store": "JsonVectorStore (Phase 5 baseline), can be replaced by FAISS/Redis later.",
    "embedding_model": "hashing-embed-v1",
    "streaming_protocol": "Server-Sent Events (SSE)",
}


def lookup_key(key: str) -> LookupResult:
    normalized = key.strip().lower().replace(" ", "_")
    value = LOOKUP_DB.get(normalized)
    return LookupResult(key=normalized, found=value is not None, value=value)


def semantic_lookup(query: str, top_k: int = 3) -> list[dict]:
    retriever = get_retriever()
    matches = retriever.retrieve(query=query, top_k=top_k)
    return [
        {
            "score": round(match.score, 4),
            "source_path": match.metadata.get("source_path"),
            "chunk_index": match.metadata.get("chunk_index"),
            "text": match.text,
        }
        for match in matches
    ]
