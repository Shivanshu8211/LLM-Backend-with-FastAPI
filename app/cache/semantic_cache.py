from __future__ import annotations

import json
import math
import threading
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from app.core.config import settings
from app.rag.embeddings import BaseEmbeddingModel, build_embedding_model


@dataclass
class CacheLookupResult:
    hit: bool
    output: str | None
    hit_type: str  # exact | semantic | miss


class CacheStats:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[str, int] = {
            'requests': 0,
            'exact_hits': 0,
            'semantic_hits': 0,
            'misses': 0,
            'writes': 0,
            'invalidations': 0,
            'errors': 0,
        }

    def inc(self, key: str) -> None:
        with self._lock:
            self._values[key] = self._values.get(key, 0) + 1

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            requests = self._values.get('requests', 0)
            hits = self._values.get('exact_hits', 0) + self._values.get('semantic_hits', 0)
            hit_ratio = (hits / requests) if requests else 0.0
            return {
                **self._values,
                'hit_ratio': round(hit_ratio, 4),
            }


class InMemoryCacheStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._items.get(key)
            if not record:
                return None
            expires_at = record.get('expires_at')
            if expires_at and expires_at <= time.time():
                self._items.pop(key, None)
                if key in self._order:
                    self._order.remove(key)
                return None
            return record

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        expires_at = time.time() + max(1, ttl_seconds)
        payload = {**value, 'expires_at': expires_at}
        with self._lock:
            if key not in self._items:
                self._order.append(key)
            self._items[key] = payload

    def keys_latest(self, limit: int) -> list[str]:
        with self._lock:
            keys = [k for k in self._order if k in self._items]
            return list(reversed(keys[-max(1, limit) :]))

    def delete(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)
            if key in self._order:
                self._order.remove(key)

    def clear(self) -> int:
        with self._lock:
            count = len(self._items)
            self._items.clear()
            self._order.clear()
            return count

    def size(self) -> int:
        with self._lock:
            return len(self._items)


class RedisSemanticCache:
    def __init__(self) -> None:
        self._stats = CacheStats()
        self._embedding_model: BaseEmbeddingModel = build_embedding_model()
        self._memory = InMemoryCacheStore()
        self._redis = self._init_redis_client()
        self._mode = settings.cache_backend.lower()
        self._namespace = settings.cache_namespace

    def _init_redis_client(self) -> Any | None:
        if not settings.cache_enabled:
            return None

        if settings.cache_backend.lower() != 'redis':
            return None

        try:
            import redis
        except Exception:
            self._stats.inc('errors')
            return None

        try:
            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            self._stats.inc('errors')
            return None

    def _exact_key(self, prompt: str) -> str:
        digest = sha256(prompt.strip().encode('utf-8')).hexdigest()
        return f'{self._namespace}:cache:exact:{digest}'

    def _zset_key(self) -> str:
        return f'{self._namespace}:cache:index'

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _read_record(self, key: str) -> dict[str, Any] | None:
        if self._redis:
            raw = self._redis.get(key)
            if not raw:
                return None
            try:
                return json.loads(raw)
            except Exception:
                self._stats.inc('errors')
                return None
        return self._memory.get(key)

    def _write_record(self, key: str, value: dict[str, Any]) -> None:
        ttl = max(1, settings.cache_ttl_seconds)
        if self._redis:
            now = time.time()
            payload = {**value, 'created_at': now}
            self._redis.setex(key, ttl, json.dumps(payload))
            self._redis.zadd(self._zset_key(), {key: now})
        else:
            self._memory.set(key, {**value, 'created_at': time.time()}, ttl_seconds=ttl)

        self._evict_if_needed()

    def _latest_keys(self, limit: int) -> list[str]:
        if self._redis:
            return self._redis.zrevrange(self._zset_key(), 0, max(0, limit - 1))
        return self._memory.keys_latest(limit=limit)

    def _delete_key(self, key: str) -> None:
        if self._redis:
            self._redis.delete(key)
            self._redis.zrem(self._zset_key(), key)
        else:
            self._memory.delete(key)

    def _evict_if_needed(self) -> None:
        max_entries = max(1, settings.cache_max_entries)
        if self._redis:
            current = self._redis.zcard(self._zset_key())
            if current <= max_entries:
                return
            over_by = current - max_entries
            oldest = self._redis.zrange(self._zset_key(), 0, over_by - 1)
            for key in oldest:
                self._delete_key(key)
        else:
            current = self._memory.size()
            if current <= max_entries:
                return
            over_by = current - max_entries
            oldest = list(reversed(self._memory.keys_latest(limit=current)))[0:over_by]
            for key in oldest:
                self._delete_key(key)

    def lookup(self, prompt: str, allow_semantic: bool = True) -> CacheLookupResult:
        if not settings.cache_enabled:
            return CacheLookupResult(hit=False, output=None, hit_type='miss')

        self._stats.inc('requests')
        exact_key = self._exact_key(prompt)
        exact_record = self._read_record(exact_key)
        if exact_record and exact_record.get('output'):
            self._stats.inc('exact_hits')
            return CacheLookupResult(hit=True, output=str(exact_record['output']), hit_type='exact')

        if not allow_semantic:
            self._stats.inc('misses')
            return CacheLookupResult(hit=False, output=None, hit_type='miss')

        query_embedding = self._embedding_model.embed_text(prompt)
        threshold = settings.cache_similarity_threshold
        best_output: str | None = None
        best_score = -1.0

        keys = self._latest_keys(limit=settings.cache_semantic_scan_limit)
        for key in keys:
            item = self._read_record(key)
            if not item:
                continue
            emb = item.get('embedding')
            out = item.get('output')
            if not emb or not out:
                continue
            score = self._cosine_similarity(query_embedding, emb)
            if score >= threshold and score > best_score:
                best_score = score
                best_output = str(out)

        if best_output is not None:
            self._stats.inc('semantic_hits')
            return CacheLookupResult(hit=True, output=best_output, hit_type='semantic')

        self._stats.inc('misses')
        return CacheLookupResult(hit=False, output=None, hit_type='miss')

    def store(self, prompt: str, output: str) -> None:
        if not settings.cache_enabled:
            return

        try:
            embedding = self._embedding_model.embed_text(prompt)
            record = {
                'prompt': prompt,
                'output': output,
                'embedding': embedding,
            }
            key = self._exact_key(prompt)
            self._write_record(key, record)
            self._stats.inc('writes')
        except Exception:
            self._stats.inc('errors')

    def clear(self) -> int:
        removed = 0
        if self._redis:
            pattern = f'{self._namespace}:cache:exact:*'
            keys = list(self._redis.scan_iter(match=pattern))
            for key in keys:
                self._delete_key(key)
                removed += 1
            self._redis.delete(self._zset_key())
        else:
            removed = self._memory.clear()
        self._stats.inc('invalidations')
        return removed

    def status(self) -> dict[str, Any]:
        backend = 'redis' if self._redis else 'memory'
        size = self._redis.zcard(self._zset_key()) if self._redis else self._memory.size()
        return {
            'enabled': settings.cache_enabled,
            'configured_backend': self._mode,
            'active_backend': backend,
            'redis_connected': self._redis is not None,
            'ttl_seconds': settings.cache_ttl_seconds,
            'max_entries': settings.cache_max_entries,
            'similarity_threshold': settings.cache_similarity_threshold,
            'semantic_scan_limit': settings.cache_semantic_scan_limit,
            'entries': int(size),
            'stats': self._stats.snapshot(),
        }
