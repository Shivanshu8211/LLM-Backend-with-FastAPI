LLM Backend (Phase 5: RAG Core)

Run server:
`uvicorn app.main:app --reload`

Set env vars (PowerShell):
`$env:GEMINI_API_KEY = "YOUR-API-KEY"`

Phase 2-4 endpoints:
- `GET /health/`
- `GET /demo/sync`
- `GET /demo/async`
- `GET /demo/metrics`
- `POST /query/sync`
- `POST /query/async`
- `POST /jobs/submit`
- `GET /jobs/{job_id}`
- `GET /stream/stream?prompt=...`

Phase 5 (RAG) endpoints:
- `GET /rag/status`
- `GET /rag/sources`
- `POST /rag/index` with body: `{"rebuild": true}`
- `POST /rag/search` with body: `{"query": "...", "top_k": 4}`
- `POST /rag/ask-sync` with body: `{"prompt": "...", "top_k": 4}`
- `POST /rag/ask-async` with body: `{"prompt": "...", "top_k": 4}`
- `POST /rag/analyze` with body:
  `{"top_k":4,"cases":[{"query":"What is FastAPI?","expected_terms":["fastapi","asgi"]}]}`

RAG workflow:
1. Add source docs under `app/rag/data/`
2. Build index via `POST /rag/index`
3. Validate retrieval via `POST /rag/search`
4. Ask grounded questions via `POST /rag/ask-async`
5. Run retrieval analysis via `POST /rag/analyze`
