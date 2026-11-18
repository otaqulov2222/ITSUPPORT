from __future__ import annotations

import base64
import time
from typing import Any

import httpx

from app.ai.providers.base import (
    SpeechToText,
    STTResult,
    TextGenerator,
    TextResult,
    VisionAnalyzer,
    VisionResult,
)
from app.core.config import get_settings


class GroqError(RuntimeError):
    pass


class GroqTextGenerator(TextGenerator):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.base_url = "https://api.groq.com/openai/v1"

    async def generate(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> TextResult:
        if not self.api_key:
            raise GroqError("GROQ_API_KEY yo'q")

        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, *messages],
        }
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise GroqError(f"Groq text error {response.status_code}: {response.text[:400]}")

        data = response.json()
        message = data["choices"][0]["message"]
        choice = (message.get("content") or "").strip()
        if not choice:
            # Some Groq models put text in reasoning and leave content empty
            choice = (message.get("reasoning") or "").strip()
        usage = data.get("usage") or {}
        return TextResult(
            text=choice,
            model=self.model,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
            raw=data,
        )


class GroqVisionAnalyzer(VisionAnalyzer):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_vision_model
        self.base_url = "https://api.groq.com/openai/v1"

    async def analyze_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
    ) -> VisionResult:
        if not self.api_key:
            raise GroqError("GROQ_API_KEY yo'q")

        b64 = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64}"
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.1,
            "max_tokens": 700,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        }
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise GroqError(f"Groq vision error {response.status_code}: {response.text[:400]}")

        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        unclear = any(
            marker in text.lower()
            for marker in ("aniq emas", "ko'rinmayapti", "unclear", "cannot read", "o'qib bo'lmadi")
        )
        usage = data.get("usage") or {}
        error_lines = [
            line.strip("-• ").strip()
            for line in text.splitlines()
            if "error" in line.lower() or "xato" in line.lower() or "ошиб" in line.lower()
        ]
        return VisionResult(
            description=text,
            error_texts=error_lines[:10],
            unclear=unclear,
            model=self.model,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            latency_ms=latency_ms,
        )


class GroqSpeechToText(SpeechToText):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_stt_model
        self.base_url = "https://api.groq.com/openai/v1"

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "audio.ogg",
        language: str | None = None,
    ) -> STTResult:
        if not self.api_key:
            raise GroqError("GROQ_API_KEY yo'q")

        files = {"file": (filename, audio_bytes)}
        data = {"model": self.model, "response_format": "json"}
        if language:
            data["language"] = language

        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=data,
                files=files,
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            raise GroqError(f"Groq STT error {response.status_code}: {response.text[:400]}")

        payload = response.json()
        return STTResult(
            text=(payload.get("text") or "").strip(),
            language=payload.get("language") or language,
            model=self.model,
            latency_ms=latency_ms,
        )
