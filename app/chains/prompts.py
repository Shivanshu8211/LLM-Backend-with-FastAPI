from __future__ import annotations


def build_tool_augmented_prompt(user_prompt: str, context: str, tool_notes: str) -> str:
    return (
        "You are a precise backend assistant.\n"
        "Use context and tool outputs when relevant. "
        "If information is missing, explicitly say so.\n\n"
        f"Retrieved Context:\n{context or '(none)'}\n\n"
        f"Tool Outputs:\n{tool_notes or '(none)'}\n\n"
        f"User Question:\n{user_prompt}\n\n"
        "Answer:"
    )
