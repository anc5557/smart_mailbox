"""
데이터 저장소 모듈

이 모듈은 이메일 데이터와 설정을 저장하고 관리하는 기능을 제공합니다.
JSON 파일을 사용하여 데이터를 영구 저장합니다.
"""

from .json_storage import JSONStorageManager, Email, Tag, AppSetting, ProcessingLog

__all__ = [
    'JSONStorageManager',
    'Email', 
    'Tag',
    'AppSetting',
    'ProcessingLog'
] 