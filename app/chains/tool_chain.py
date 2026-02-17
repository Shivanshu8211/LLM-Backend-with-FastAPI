from __future__ import annotations

import asyncio
import re
import threading
import time
from dataclasses import asdict, dataclass

from app.chains.langchain_adapter import detect_langchain_support, try_format_with_langchain
from app.chains.prompts import build_tool_augmented_prompt
from app.chains.rag_chain import retrieve_context
from app.core.config import settings
from app.llm.inference import run_completion_sync
from app.tools.calculator import calculate
from app.tools.lookup import lookup_key, semantic_lookup


@dataclass
class ToolInvocation:
    tool_name: str
    tool_input: str
    success: bool
    output: str
    ts: float


class ToolInvocationLog:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: list[ToolInvocation] = []

    def add(self, item: ToolInvocation) -> None:
        with self._lock:
            self._items.append(item)
            if len(self._items) > 500:
                self._items = self._items[-500:]

    def latest(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return [asdict(item) for item in self._items[-max(1, limit) :]]


class ToolOrchestrator:
    def __init__(self) -> None:
        self._log = ToolInvocationLog()

    @property
    def tool_names(self) -> list[str]:
        return ["calculator", "lookup_key", "semantic_lookup"]

    def get_logs(self, limit: int = 50) -> list[dict]:
        return self._log.latest(limit=limit)

    def _extract_math_expression(self, prompt: str) -> str | None:
        match = re.search(r"([-+*/(). 0-9]{3,})", prompt)
        if not match:
            return None
        expr = match.group(1).strip()
        if any(ch.isdigit() for ch in expr):
            return expr
        return None

    def _extract_lookup_key(self, prompt: str) -> str | None:
        lowered = prompt.lower()
        prefixes = ["lookup", "find key", "what is key", "db key"]
        for prefix in prefixes:
            if prefix in lowered:
                idx = lowered.find(prefix) + len(prefix)
                candidate = prompt[idx:].strip(" :?")
                if candidate:
                    return candidate
        return None

    def _invoke_tools(self, prompt: str, top_k: int) -> list[str]:
        notes: list[str] = []
        calls = 0

        expr = self._extract_math_expression(prompt)
        if expr and calls < settings.tool_max_invocations_per_request:
            result = calculate(expr)
            calls += 1
            if result.ok:
                text = f"calculator({expr}) = {result.result}"
                self._log.add(ToolInvocation("calculator", expr, True, text, time.time()))
            else:
                text = f"calculator({expr}) failed: {result.error}"
                self._log.add(ToolInvocation("calculator", expr, False, text, time.time()))
            notes.append(text)

        lookup_key_candidate = self._extract_lookup_key(prompt)
        if lookup_key_candidate and calls < settings.tool_max_invocations_per_request:
            hit = lookup_key(lookup_key_candidate)
            calls += 1
            if hit.found:
                text = f"lookup_key({hit.key}) -> {hit.value}"
                self._log.add(ToolInvocation("lookup_key", hit.key, True, text, time.time()))
            else:
                text = f"lookup_key({hit.key}) -> not found"
                self._log.add(ToolInvocation("lookup_key", hit.key, False, text, time.time()))
            notes.append(text)

        if calls < settings.tool_max_invocations_per_request:
            semantic_hits = semantic_lookup(prompt, top_k=min(top_k, 3))
            if semantic_hits:
                top = semantic_hits[0]
                text = f"semantic_lookup(top1) score={top['score']} source={top['source_path']}"
                self._log.add(ToolInvocation("semantic_lookup", prompt, True, text, time.time()))
                notes.append(text)

        return notes

    def run_sync(self, prompt: str, top_k: int, use_rag: bool, use_tools: bool) -> dict:
        context = ""
        retrieved: list[dict] = []
        tool_notes: list[str] = []

        if use_rag:
            context, retrieved = retrieve_context(prompt, top_k=top_k)

        if use_tools:
            tool_notes = self._invoke_tools(prompt, top_k=top_k)

        final_prompt = build_tool_augmented_prompt(
            user_prompt=prompt,
            context=context,
            tool_notes="\n".join(tool_notes),
        )

        lc = detect_langchain_support()
        if settings.chain_mode.lower() == "langchain":
            final_prompt = try_format_with_langchain(
                system_prompt="You are a tool-aware RAG assistant.",
                user_prompt=final_prompt,
            )

        output = run_completion_sync(final_prompt)

        return {
            "mode": "chain-sync",
            "chain_mode": "langchain" if settings.chain_mode.lower() == "langchain" else "native",
            "langchain_available": lc.available,
            "langchain_reason": lc.reason,
            "output": output,
            "retrieved": retrieved,
            "tool_notes": tool_notes,
            "tools_used": len(tool_notes),
        }

    async def run_async(self, prompt: str, top_k: int, use_rag: bool, use_tools: bool) -> dict:
        return await asyncio.to_thread(self.run_sync, prompt, top_k, use_rag, use_tools)
