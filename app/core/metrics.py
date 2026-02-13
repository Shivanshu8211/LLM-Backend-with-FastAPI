import threading
import time
from dataclasses import dataclass, field


@dataclass
class StreamMetrics:
    started_at: float = field(default_factory=time.perf_counter)
    first_token_at: float | None = None

    def mark_first_token(self) -> None:
        if self.first_token_at is None:
            self.first_token_at = time.perf_counter()

    @property
    def ttft_seconds(self) -> float | None:
        if self.first_token_at is None:
            return None
        return self.first_token_at - self.started_at

    @property
    def total_seconds(self) -> float:
        return time.perf_counter() - self.started_at


class RouteLatencyRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: dict[str, int] = {}
        self._totals: dict[str, float] = {}

    def observe(self, route: str, seconds: float) -> None:
        with self._lock:
            self._counts[route] = self._counts.get(route, 0) + 1
            self._totals[route] = self._totals.get(route, 0.0) + seconds

    def snapshot(self) -> dict[str, dict[str, float | int]]:
        with self._lock:
            result: dict[str, dict[str, float | int]] = {}
            for route, count in self._counts.items():
                total = self._totals.get(route, 0.0)
                result[route] = {
                    'count': count,
                    'avg_seconds': (total / count) if count else 0.0,
                }
            return result


route_latency_registry = RouteLatencyRegistry()
