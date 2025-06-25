"""
AI 모듈

이 모듈은 Ollama를 통한 LLM 연동과 이메일 자동 태깅, 답장 생성 기능을 제공합니다.
"""

from .ollama_client import OllamaClient, OllamaConfig, EmailTagger, ReplyGenerator
from .tagger import EmailTaggingManager, BatchProcessor

__all__ = [
    'OllamaClient',
    'OllamaConfig', 
    'EmailTagger',
    'ReplyGenerator',
    'EmailTaggingManager',
    'BatchProcessor'
] 