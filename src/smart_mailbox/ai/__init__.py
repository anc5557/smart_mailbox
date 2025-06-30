"""
AI 모듈

이 모듈은 Ollama를 통한 LLM 연동과 이메일 자동 태깅, 답장 생성 기능을 제공합니다.
"""

from .ollama_client import OllamaClient, EmailTagger, ReplyGenerator
from .tagger import Tagger

__all__ = [
    'OllamaClient',
    'EmailTagger',
    'ReplyGenerator',
    'Tagger'
] 