from __future__ import annotations

from app.core.config import settings
from app.llm.inference import run_completion, run_completion_sync
from app.rag.retriever import RagRetriever


def build_grounded_prompt(user_prompt: str, context: str) -> str:
    return (
        'You are a helpful assistant. Use only the provided context. '
        'If context is insufficient, clearly say what is missing.\n\n'
        f'Context:\n{context}\n\n'
        f'User Question:\n{user_prompt}\n\n'
        'Answer:'
    )


def rag_answer_sync(retriever: RagRetriever, prompt: str, top_k: int | None = None) -> dict:
    k = top_k or settings.rag_default_top_k
    context, results = retriever.build_context(query=prompt, top_k=k)
    grounded_prompt = build_grounded_prompt(prompt, context)
    output = run_completion_sync(grounded_prompt)

    return {
        'output': output,
        'retrieved': [
            {
                'score': round(item.score, 4),
                'source_path': item.metadata.get('source_path'),
                'chunk_index': item.metadata.get('chunk_index'),
                'text': item.text,
            }
            for item in results
        ],
        'used_top_k': k,
    }


async def rag_answer_async(retriever: RagRetriever, prompt: str, top_k: int | None = None) -> dict:
    k = top_k or settings.rag_default_top_k
    context, results = retriever.build_context(query=prompt, top_k=k)
    grounded_prompt = build_grounded_prompt(prompt, context)
    output = await run_completion(grounded_prompt)

    return {
        'output': output,
        'retrieved': [
            {
                'score': round(item.score, 4),
                'source_path': item.metadata.get('source_path'),
                'chunk_index': item.metadata.get('chunk_index'),
                'text': item.text,
            }
            for item in results
        ],
        'used_top_k': k,
    }
