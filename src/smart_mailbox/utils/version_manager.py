"""
버전 정보 관리 모듈
"""
import sys
import platform
from typing import Dict, Any
from importlib.metadata import version


class VersionManager:
    """애플리케이션 버전 관리"""
    
    def __init__(self):
        self._current_version = None
        self._load_version()
    
    def _load_version(self):
        """패키지에서 버전 정보를 로드합니다."""
        try:
            # 설치된 패키지에서 버전 가져오기
            self._current_version = version("smart-mailbox")
        except Exception:
            try:
                # 개발 모드에서는 __init__.py에서 가져오기
                from smart_mailbox import __version__
                self._current_version = __version__
            except ImportError:
                # 모든 방법이 실패하면 기본값
                self._current_version = "0.0.0"

    def get_current_version(self) -> str:
        """현재 애플리케이션 버전을 반환합니다."""
        return self._current_version or "0.0.0"
    
    def get_version_info(self) -> Dict[str, Any]:
        """상세한 버전 정보를 반환합니다."""
        return {
            "version": self.get_current_version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.system(),
            "architecture": platform.machine()
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
            from packaging import version as pkg_version
            v1 = pkg_version.parse(version1)
            v2 = pkg_version.parse(version2)
            
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception:
            # packaging 파싱에 실패하면 문자열 비교로 폴백
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

    def print_version_info(self):
        """버전 정보를 콘솔에 출력합니다. (디버깅용)"""
        info = self.get_version_info()
        print(f"Smart Mailbox v{info['version']}")
        print(f"Python {info['python_version']}")
        print(f"Platform: {info['platform']} ({info['architecture']})")


# 편의 함수들
def get_version() -> str:
    """현재 버전을 반환하는 편의 함수"""
    vm = VersionManager()
    return vm.get_current_version()

def print_version():
    """버전 정보를 출력하는 편의 함수"""
    vm = VersionManager()
    vm.print_version_info()


if __name__ == "__main__":
    # 스크립트로 직접 실행할 때 버전 정보 출력
    print_version() 