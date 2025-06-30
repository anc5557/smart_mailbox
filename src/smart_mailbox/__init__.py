"""
AI Smart Mailbox - 이메일 자동 태깅 및 답장 생성 도구
"""

try:
    from importlib.metadata import version
    __version__ = version("smart-mailbox")
except ImportError:
    # Python < 3.8 또는 패키지가 설치되지 않은 경우
    __version__ = "0.0.0"

__author__ = "Smart Mailbox Team"
__description__ = "AI 기반 이메일 자동 분석 및 답장 생성 데스크탑 애플리케이션"

__all__ = ['__version__', '__author__', '__description__'] 