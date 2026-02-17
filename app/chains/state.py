from __future__ import annotations

import threading

from app.chains.tool_chain import ToolOrchestrator

_orchestrator_lock = threading.Lock()
_orchestrator: ToolOrchestrator | None = None


def get_orchestrator() -> ToolOrchestrator:
    global _orchestrator
    with _orchestrator_lock:
        if _orchestrator is None:
            _orchestrator = ToolOrchestrator()
        return _orchestrator
