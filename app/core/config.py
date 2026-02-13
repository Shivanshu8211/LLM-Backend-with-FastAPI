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


settings = Settings()
