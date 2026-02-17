LLM Backend (Phase 6: RAG + Tool Calling)

Run server:
`uvicorn app.main:app --reload`

UI:
- Open `http://127.0.0.1:8000/` for the integrated dashboard.
- Static frontend assets are served under `/ui`.

Set env vars (PowerShell):
`$env:GEMINI_API_KEY = "YOUR-API-KEY"`
`$env:CHAIN_MODE = "native"`  # or "langchain" (if langchain_core installed)

Phase 5 RAG endpoints:
- `GET /rag/status`
- `POST /rag/index`
- `POST /rag/search`
- `POST /rag/ask-async`
- `POST /rag/analyze`

Phase 6 chain + tool-calling endpoints:
- `GET /chains/status`
- `POST /chains/ask-sync`
- `POST /chains/ask-async`
- `GET /chains/tools/logs`

Sample chain request:
`curl.exe -X POST "http://127.0.0.1:8000/chains/ask-async" -H "Content-Type: application/json" -d "{\"prompt\":\"What is FastAPI and compute 12*7\",\"top_k\":3,\"use_rag\":true,\"use_tools\":true}"`

Phase 6 workflow:
1. Index docs with `POST /rag/index`
2. Ask through `/chains/ask-async` to use retrieval + tools + LLM
3. Inspect tool invocation traces via `/chains/tools/logs`
