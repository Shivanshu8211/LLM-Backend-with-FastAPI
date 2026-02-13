LLM Backend (Phase 4 Baseline)

Run server:
`uvicorn app.main:app --reload`

Set env vars (PowerShell):
`$env:GEMINI_API_KEY = "YOUR-API-KEY"`

Core endpoints:
- `GET /health/`
- `GET /demo/sync`
- `GET /demo/async`
- `GET /demo/metrics`
- `POST /query/sync`
- `POST /query/async`
- `POST /jobs/submit`
- `GET /jobs/{job_id}`
- `GET /stream/stream?prompt=...`

Streaming test:
`curl.exe -N -H "Accept: text/event-stream" "http://localhost:8000/stream/stream?prompt=Explain%20API%20in%2020%20words"`
