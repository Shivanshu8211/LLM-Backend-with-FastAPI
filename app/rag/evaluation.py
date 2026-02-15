from __future__ import annotations

from dataclasses import dataclass

from app.rag.retriever import RagRetriever


@dataclass
class RetrievalEvalCase:
    query: str
    expected_terms: list[str]


@dataclass
class RetrievalEvalResult:
    query: str
    found: bool
    top_match_score: float


def evaluate_retrieval(retriever: RagRetriever, cases: list[RetrievalEvalCase], top_k: int) -> dict:
    results: list[RetrievalEvalResult] = []

    for case in cases:
        retrieved = retriever.retrieve(case.query, top_k=top_k)
        combined_text = ' '.join(item.text.lower() for item in retrieved)
        found = any(term.lower() in combined_text for term in case.expected_terms)
        top_score = retrieved[0].score if retrieved else 0.0
        results.append(
            RetrievalEvalResult(
                query=case.query,
                found=found,
                top_match_score=top_score,
            )
        )

    total = len(results)
    hits = sum(1 for r in results if r.found)
    hit_rate = (hits / total) if total else 0.0

    return {
        'cases': total,
        'hits': hits,
        'hit_rate': round(hit_rate, 4),
        'details': [
            {
                'query': r.query,
                'found_expected_term': r.found,
                'top_match_score': round(r.top_match_score, 4),
            }
            for r in results
        ],
    }
