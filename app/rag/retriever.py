from __future__ import annotations

from dataclasses import dataclass

from app.rag.embeddings import BaseEmbeddingModel
from app.rag.vector_store import JsonVectorStore, RetrievalResult, VectorRecord


@dataclass
class IndexStats:
    indexed_chunks: int
    embedding_model: str
    embedding_dimension: int


class RagRetriever:
    def __init__(self, embedding_model: BaseEmbeddingModel, vector_store: JsonVectorStore) -> None:
        self._embedding_model = embedding_model
        self._vector_store = vector_store

    @property
    def embedding_model_name(self) -> str:
        return self._embedding_model.model_name

    @property
    def index_size(self) -> int:
        return self._vector_store.size

    def index_chunks(self, chunks: list[dict], rebuild: bool = False) -> IndexStats:
        if rebuild:
            self._vector_store.clear()

        embeddings = self._embedding_model.embed_batch([item['text'] for item in chunks])
        records = []
        for item, emb in zip(chunks, embeddings):
            records.append(
                VectorRecord(
                    record_id=item['chunk_id'],
                    text=item['text'],
                    embedding=emb,
                    metadata=item['metadata'],
                )
            )

        self._vector_store.upsert_many(records)
        self._vector_store.save()

        return IndexStats(
            indexed_chunks=self._vector_store.size,
            embedding_model=self._embedding_model.model_name,
            embedding_dimension=self._embedding_model.dimension,
        )

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievalResult]:
        query_embedding = self._embedding_model.embed_text(query)
        return self._vector_store.search(query_embedding=query_embedding, top_k=top_k)

    def build_context(self, query: str, top_k: int = 4, max_chars: int = 3000) -> tuple[str, list[RetrievalResult]]:
        results = self.retrieve(query=query, top_k=top_k)

        context_lines: list[str] = []
        current_len = 0
        for idx, res in enumerate(results, start=1):
            source = res.metadata.get('source_path', 'unknown')
            line = f'[{idx}] (score={res.score:.3f}, source={source}) {res.text}'
            if current_len + len(line) > max_chars:
                break
            context_lines.append(line)
            current_len += len(line)

        context = '\n'.join(context_lines)
        return context, results
