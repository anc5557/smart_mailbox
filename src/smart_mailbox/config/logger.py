import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class LoggerSetup:
    """애플리케이션 로깅 설정 관리"""
    
    @staticmethod
    def setup_logger(name: str = "smart_mailbox") -> logging.Logger:
        """
        애플리케이션 로거 설정
        
        Args:
            name: 로거 이름
            
        Returns:
            설정된 로거 인스턴스
        """
        logger = logging.getLogger(name)
        
        # 이미 핸들러가 설정되어 있으면 중복 설정 방지
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.DEBUG)
        
        # 로그 디렉토리 생성
        log_dir = Path.home() / ".smart_mailbox" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 로그 파일명 (날짜별)
        log_file = log_dir / f"smart_mailbox_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 파일 핸들러 설정 (10MB, 5개 백업)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷 설정
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        # 핸들러 추가
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger


class UserActionLogger:
    """사용자 행위 전용 로거"""
    
    def __init__(self):
        self.logger = logging.getLogger("smart_mailbox.user_actions")
        
        # 이미 핸들러가 설정되어 있으면 중복 설정 방지
        if self.logger.handlers:
            return
            
        self.logger.setLevel(logging.INFO)
        
        # 사용자 행위 전용 로그 파일
        log_dir = Path.home() / ".smart_mailbox" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        action_log_file = log_dir / f"user_actions_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 파일 핸들러 설정
        file_handler = logging.handlers.RotatingFileHandler(
            action_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,  # 사용자 행위는 더 많이 보관
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # 사용자 행위 전용 포맷
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log_upload(self, file_path: str, email_data: Dict[str, Any], ai_result: Optional[Dict[str, Any]] = None):
        """이메일 업로드 로그"""
        msg = f"EMAIL_UPLOAD: {file_path}"
        msg += f"\n  제목: {email_data.get('subject', 'N/A')}"
        msg += f"\n  발신자: {email_data.get('sender', 'N/A')}"
        msg += f"\n  날짜: {email_data.get('date_sent', 'N/A')}"
        if ai_result:
            msg += f"\n  AI 분석 결과:"
            msg += f"\n    - 태그: {ai_result.get('tags', [])}"
            msg += f"\n    - 처리 시간: {ai_result.get('processing_time', 'N/A')}초"
            msg += f"\n    - 모델: {ai_result.get('model', 'N/A')}"
        self.logger.info(msg)
    
    def log_delete(self, email_id: str, email_subject: str):
        """이메일 삭제 로그"""
        self.logger.info(f"EMAIL_DELETE: ID={email_id}, 제목='{email_subject}'")
    
    def log_settings_change(self, setting_type: str, old_value: str, new_value: str):
        """설정 변경 로그"""
        self.logger.info(f"SETTINGS_CHANGE: {setting_type} - '{old_value}' → '{new_value}'")
    
    def log_tag_change(self, action: str, tag_name: str, email_id: Optional[str] = None):
        """태그 변경 로그"""
        if email_id:
            self.logger.info(f"TAG_{action.upper()}: 태그='{tag_name}', 이메일 ID={email_id}")
        else:
            self.logger.info(f"TAG_{action.upper()}: 태그='{tag_name}'")
    
    def log_ai_request(self, request_type: str, email_id: str, details: Optional[Dict[str, Any]] = None):
        """AI 요청 로그"""
        msg = f"AI_REQUEST: {request_type} - 이메일 ID={email_id}"
        if details:
            for key, value in details.items():
                msg += f"\n  {key}: {value}"
        self.logger.info(msg)
    
    def log_reply_generation(self, email_id: str, email_subject: str, reply_generated: bool, reply_length: int = 0):
        """답장 생성 로그"""
        status = "성공" if reply_generated else "실패"
        msg = f"REPLY_GENERATION: {status} - 이메일 ID={email_id}, 제목='{email_subject}'"
        if reply_generated:
            msg += f", 답장 길이={reply_length}자"
        self.logger.info(msg)


# 전역 로거 인스턴스
logger = LoggerSetup.setup_logger()
user_action_logger = UserActionLogger() 