"""
데이터 저장소 모듈

이 모듈은 이메일 데이터와 설정을 저장하고 관리하는 기능을 제공합니다.
SQLite 데이터베이스를 사용하여 데이터를 영구 저장합니다.
"""

from .database import DatabaseManager
from .models import Base, Email, Tag, AppSettings, ProcessingLog

__all__ = [
    'DatabaseManager',
    'Base',
    'Email', 
    'Tag',
    'AppSettings',
    'ProcessingLog'
] 