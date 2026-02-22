from __future__ import annotations

import threading

from app.cache.semantic_cache import RedisSemanticCache

_cache_lock = threading.Lock()
_cache: RedisSemanticCache | None = None


def get_cache() -> RedisSemanticCache:
    global _cache
    with _cache_lock:
        if _cache is None:
            _cache = RedisSemanticCache()
        return _cache
