from __future__ import annotations

from app.ai.providers.base import SpeechToText, TextGenerator, VisionAnalyzer
from app.ai.providers.groq_provider import GroqSpeechToText, GroqTextGenerator, GroqVisionAnalyzer
from app.core.config import get_settings


def get_text_generator() -> TextGenerator:
    settings = get_settings()
    if settings.ai_provider == "groq":
        return GroqTextGenerator()
    # Default / fallback path still Groq for Phase 3
    return GroqTextGenerator()


def get_vision_analyzer() -> VisionAnalyzer:
    return GroqVisionAnalyzer()


def get_stt() -> SpeechToText:
    return GroqSpeechToText()
