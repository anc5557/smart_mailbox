# src/smart_mailbox/storage/file_manager.py
import os
import hashlib
from pathlib import Path
from typing import Optional, Union
from ..config.logger import logger

class FileManager:
    """
    애플리케이션의 데이터 파일 및 디렉토리 구조를 관리하는 클래스.
    사용자 홈 디렉토리 하위에 앱 전용 폴더를 생성하고 관리합니다.
    """
    def __init__(self, app_name: str = ".smart_mailbox"):
        self.app_name = app_name
        self.base_dir = Path.home() / self.app_name
        self.config_path = self.base_dir / "config.json"
        self.tags_config_path = self.base_dir # tags.json은 이 디렉토리에 저장됩니다.
        self.emails_dir = self.base_dir / "emails"
        self.logs_dir = self.base_dir / "logs"
        
        self._create_initial_structure()

    def _create_initial_structure(self):
        """
        필요한 모든 디렉토리를 생성합니다.
        """
        try:
            self.base_dir.mkdir(exist_ok=True)
            self.emails_dir.mkdir(exist_ok=True)
            self.logs_dir.mkdir(exist_ok=True)
            logger.info(f"데이터 디렉토리 확인/생성 완료: {self.base_dir}")
        except Exception as e:
            logger.error(f"데이터 디렉토리 생성에 실패했습니다. {e}")
            # 여기서 적절한 예외 처리를 하거나 프로그램을 종료할 수 있습니다.
            raise

    def get_base_dir(self) -> Path:
        """
        애플리케이션의 기본 데이터 디렉토리 경로를 반환합니다.
        """
        return self.base_dir

    def get_data_dir(self) -> str:
        """
        JSON 데이터 파일들이 저장될 디렉토리 경로를 반환합니다.
        """
        return str(self.base_dir)

    def get_config_path(self) -> Path:
        """
        메인 설정 파일(config.json)의 전체 경로를 반환합니다.
        """
        return self.config_path
    
    def get_tags_config_path(self) -> Path:
        """
        태그 설정 파일(tags.json)이 저장될 디렉토리 경로를 반환합니다.
        """
        return self.tags_config_path

    def get_emails_dir(self) -> Path:
        """
        처리된 이메일 파일이 저장될 디렉토리 경로를 반환합니다.
        """
        return self.emails_dir

    def get_logs_dir(self) -> Path:
        """
        로그 파일이 저장될 디렉토리 경로를 반환합니다.
        """
        return self.logs_dir

    def save_email_file(self, original_path: str, content: bytes) -> Path:
        """
        처리된 .eml 파일을 emails 디렉토리에 저장합니다.
        파일 이름은 원본 파일 이름을 유지하되, 충돌을 피하기 위해 고유 ID를 추가할 수 있습니다.
        
        :param original_path: 원본 .eml 파일의 경로
        :param content: 저장할 파일의 내용 (bytes)
        :return: 저장된 파일의 Path 객체
        """
        original_filename = Path(original_path).name
        filename_stem = Path(original_filename).stem
        filename_suffix = Path(original_filename).suffix
        
        # 파일명 중복 처리
        target_path = self.emails_dir / original_filename
        counter = 1
        
        while target_path.exists():
            # 중복되는 경우 파일명에 번호 추가 (예: email_1.eml)
            new_filename = f"{filename_stem}_{counter}{filename_suffix}"
            target_path = self.emails_dir / new_filename
            counter += 1
        
        try:
            with open(target_path, 'wb') as f:
                f.write(content)
            logger.info(f"이메일 파일 저장 완료: {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"이메일 파일 저장에 실패했습니다. {e}")
            raise

# 이 클래스는 주로 다른 모듈에서 인스턴스화하여 사용됩니다.
# 예시:
# file_manager = FileManager()
# data_dir = file_manager.get_data_dir()
