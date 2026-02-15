from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from app.core.config import settings

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


class BaseEmbeddingModel(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


class HashingEmbeddingModel(BaseEmbeddingModel):
    def __init__(self, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError('dimension must be > 0')
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return 'hashing-embed-v1'

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        vec = [0.0] * self._dimension
        tokens = TOKEN_PATTERN.findall(text.lower())
        if not tokens:
            return vec

        for token in tokens:
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            idx = int.from_bytes(digest[:4], 'little') % self._dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign

        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            return vec
        return [x / norm for x in vec]


def build_embedding_model() -> BaseEmbeddingModel:
    # Keep this pluggable for future model upgrades (OpenAI/HF/Gemini embeddings).
    if settings.embedding_model.lower() == 'hashing-embed-v1':
        return HashingEmbeddingModel(dimension=settings.embedding_dimension)

    # Safe fallback to avoid startup failure if unsupported model name is configured.
    return HashingEmbeddingModel(dimension=settings.embedding_dimension)
