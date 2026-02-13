from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator


class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream(self, prompt: str) -> Generator[str, None, None]:
        raise NotImplementedError
