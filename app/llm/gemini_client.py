from __future__ import annotations

import time
from typing import Generator

from app.core.config import settings
from app.llm.provider import BaseLLMProvider


class SimulatedLLMProvider(BaseLLMProvider):
    def complete(self, prompt: str) -> str:
        if settings.simulated_inference_delay_seconds > 0:
            time.sleep(settings.simulated_inference_delay_seconds)
        return f'[SIMULATED] Completion for: {prompt}'

    def stream(self, prompt: str) -> Generator[str, None, None]:
        text = self.complete(prompt)
        for token in text.split(' '):
            if settings.simulated_inference_delay_seconds > 0:
                time.sleep(min(settings.simulated_inference_delay_seconds, 0.1))
            yield token + ' '


class GeminiLLMProvider(BaseLLMProvider):
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            print("GEMINI_API_KEY is not set")
            raise ValueError('GEMINI_API_KEY is not set')

        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                'google-generativeai package is required for Gemini provider'
            ) from exc

        genai.configure(api_key=settings.gemini_api_key)
        self._model = genai.GenerativeModel(settings.llm_model)

    def complete(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        text = getattr(response, 'text', None)
        return text or ''

    def stream(self, prompt: str) -> Generator[str, None, None]:
        response = self._model.generate_content(prompt, stream=True)
        for chunk in response:
            text = getattr(chunk, 'text', None)
            if text:
                yield text


def build_llm_provider() -> BaseLLMProvider:
    provider_name = settings.llm_provider.lower()

    if provider_name == 'gemini':
        try:
            return GeminiLLMProvider()
        except Exception:
            return SimulatedLLMProvider()

    return SimulatedLLMProvider()
