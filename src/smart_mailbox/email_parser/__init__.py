"""
AI Smart Mailbox 이메일 처리 모듈

이 모듈은 .eml 파일 파싱과 이메일 데이터 분석 기능을 제공합니다.
"""

from .parser import EmailParser, parse_email_file, is_valid_email_file

__all__ = [
    'EmailParser',
    'parse_email_file', 
    'is_valid_email_file'
] 