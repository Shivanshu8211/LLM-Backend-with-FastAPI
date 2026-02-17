from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', case_sensitive=False)

    app_name: str = 'LLM Backend'
    env: str = 'dev'
    log_level: str = 'INFO'

    llm_provider: str = 'gemini'
    llm_model: str = 'gemini-2.5-flash'
    gemini_api_key: str | None = None
    llm_timeout_seconds: int = 60

    worker_concurrency: int = 4
    simulated_inference_delay_seconds: float = 0.0

    # Phase 5 (RAG)
    embedding_model: str = 'hashing-embed-v1'
    embedding_dimension: int = 384
    rag_default_top_k: int = 4
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_data_dir: str = 'app/rag/data'
    vector_store_path: str = 'app/rag/vector_store.json'

    # Phase 6 (chains and tool calling)
    chain_mode: str = 'native'  # native | langchain
    chain_max_context_chars: int = 3000
    tool_max_invocations_per_request: int = 2


settings = Settings()
