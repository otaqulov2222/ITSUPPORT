from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextResult:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisionResult:
    description: str
    error_texts: list[str] = field(default_factory=list)
    unclear: bool = False
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


@dataclass
class STTResult:
    text: str
    language: str | None = None
    model: str = ""
    latency_ms: int = 0


class TextGenerator(ABC):
    @abstractmethod
    async def generate(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> TextResult:
        raise NotImplementedError


class VisionAnalyzer(ABC):
    @abstractmethod
    async def analyze_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
    ) -> VisionResult:
        raise NotImplementedError


class SpeechToText(ABC):
    @abstractmethod
    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "audio.ogg",
        language: str | None = None,
    ) -> STTResult:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
