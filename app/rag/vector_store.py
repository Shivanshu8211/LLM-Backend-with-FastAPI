from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VectorRecord:
    record_id: str
    text: str
    embedding: list[float]
    metadata: dict


@dataclass
class RetrievalResult:
    record_id: str
    text: str
    score: float
    metadata: dict


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    n1 = math.sqrt(sum(a * a for a in vec1))
    n2 = math.sqrt(sum(b * b for b in vec2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


class JsonVectorStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._records: list[VectorRecord] = []
        self._dim: int | None = None
        self.load()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._records)

    @property
    def dimension(self) -> int | None:
        with self._lock:
            return self._dim

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._dim = None

    def upsert_many(self, records: list[VectorRecord]) -> None:
        if not records:
            return

        with self._lock:
            if self._dim is None:
                self._dim = len(records[0].embedding)

            indexed = {rec.record_id: rec for rec in self._records}
            for rec in records:
                if len(rec.embedding) != self._dim:
                    raise ValueError('Embedding dimension mismatch')
                indexed[rec.record_id] = rec

            self._records = list(indexed.values())

    def search(self, query_embedding: list[float], top_k: int = 4) -> list[RetrievalResult]:
        with self._lock:
            scored: list[RetrievalResult] = []
            for rec in self._records:
                score = cosine_similarity(query_embedding, rec.embedding)
                scored.append(
                    RetrievalResult(
                        record_id=rec.record_id,
                        text=rec.text,
                        score=score,
                        metadata=rec.metadata,
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[: max(1, top_k)]

    def save(self) -> None:
        with self._lock:
            payload = {
                'dimension': self._dim,
                'records': [
                    {
                        'record_id': rec.record_id,
                        'text': rec.text,
                        'embedding': rec.embedding,
                        'metadata': rec.metadata,
                    }
                    for rec in self._records
                ],
            }

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(payload), encoding='utf-8')

    def load(self) -> None:
        if not self._path.exists():
            return

        payload = json.loads(self._path.read_text(encoding='utf-8'))
        records = []
        for item in payload.get('records', []):
            records.append(
                VectorRecord(
                    record_id=item['record_id'],
                    text=item['text'],
                    embedding=item['embedding'],
                    metadata=item.get('metadata', {}),
                )
            )

        with self._lock:
            self._dim = payload.get('dimension')
            self._records = records
