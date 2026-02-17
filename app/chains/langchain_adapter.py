from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LangChainSupport:
    available: bool
    reason: str


def detect_langchain_support() -> LangChainSupport:
    try:
        from langchain_core.prompts import ChatPromptTemplate  # noqa: F401

        return LangChainSupport(available=True, reason="langchain_core detected")
    except Exception as exc:
        return LangChainSupport(available=False, reason=f"fallback to native prompts: {exc}")


def try_format_with_langchain(system_prompt: str, user_prompt: str) -> str:
    try:
        from langchain_core.prompts import ChatPromptTemplate

        template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("human", "{user_prompt}"),
            ]
        )
        rendered = template.format(system_prompt=system_prompt, user_prompt=user_prompt)
        return rendered
    except Exception:
        return f"{system_prompt}\n\n{user_prompt}"
