LLM Backend

How to start server:
    1. Navigate to main directory, the execute the below command
    `uvicorn app.main:app --reload`
How to set env-var:
    `$env:GEMINI_API_KEY = "YOUR-API-KEY"`
How to test tokenized streaming nature of API:
    `curl.exe -N -H "Accept: text/event-stream" "http://localhost:8000/stream/stream?prompt=Explain%20API%20in%2020%20words"`