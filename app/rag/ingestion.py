from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


@dataclass
class SourceChunk:
    chunk_id: str
    text: str
    metadata: dict


def _is_supported(path: Path) -> bool:
    return path.suffix.lower() in {'.txt', '.md', '.rst', '.py'}


def collect_documents(data_dir: str | None = None) -> list[Path]:
    root = Path(data_dir or settings.rag_data_dir)
    if not root.exists():
        return []

    paths = [p for p in root.rglob('*') if p.is_file() and _is_supported(p)]
    paths.sort()
    return paths


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    clean = ' '.join(text.split())
    if not clean:
        return []

    if overlap >= chunk_size:
        overlap = max(0, chunk_size // 4)

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(0, end - overlap)

    return chunks


def build_chunks(
    data_dir: str | None = None,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[SourceChunk]:
    chunk_size = chunk_size or settings.rag_chunk_size
    overlap = overlap or settings.rag_chunk_overlap

    chunks: list[SourceChunk] = []
    for path in collect_documents(data_dir=data_dir):
        text = path.read_text(encoding='utf-8', errors='ignore')
        parts = chunk_text(text=text, chunk_size=chunk_size, overlap=overlap)

        for idx, chunk in enumerate(parts):
            raw_id = f'{path.as_posix()}::{idx}::{chunk}'
            chunk_id = hashlib.sha1(raw_id.encode('utf-8')).hexdigest()
            chunks.append(
                SourceChunk(
                    chunk_id=chunk_id,
                    text=chunk,
                    metadata={
                        'source_path': str(path),
                        'chunk_index': idx,
                    },
                )
            )

    return chunks
