"""
버전 정보 관리 모듈
"""
import sys
from pathlib import Path
from typing import Dict, Any
from packaging import version


class VersionManager:
    """애플리케이션 버전 정보를 관리하는 클래스"""
    
    def __init__(self):
        self._current_version = None
        self._load_version()
    
    def _load_version(self):
        """현재 애플리케이션 버전을 로드합니다."""
        try:
            # __init__.py에서 버전 정보 가져오기
            from smart_mailbox import __version__
            self._current_version = __version__
        except ImportError:
            # 패키지가 설치되지 않은 경우 기본값 사용
            self._current_version = "0.3.0"
    
    def get_current_version(self) -> str:
        """현재 애플리케이션 버전을 반환합니다."""
        return self._current_version or "0.3.0"
    
    def get_version_info(self) -> Dict[str, Any]:
        """상세한 버전 정보를 반환합니다."""
        return {
            "version": self.get_current_version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "architecture": sys.maxsize > 2**32 and "64bit" or "32bit"
        }
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        두 버전을 비교합니다.
        
        Args:
            version1: 첫 번째 버전
            version2: 두 번째 버전
            
        Returns:
            -1: version1 < version2
             0: version1 == version2
             1: version1 > version2
        """
        try:
            v1 = version.parse(version1)
            v2 = version.parse(version2)
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception:
            # 버전 파싱 실패 시 문자열 비교
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def is_newer_version(self, remote_version: str) -> bool:
        """
        원격 버전이 현재 버전보다 새로운지 확인합니다.
        
        Args:
            remote_version: 확인할 원격 버전
            
        Returns:
            bool: 원격 버전이 더 새로우면 True
        """
        return self.compare_versions(self.get_current_version(), remote_version) < 0 