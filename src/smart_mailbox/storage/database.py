"""
데이터베이스 연결 및 관리
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Email, Tag, AppSettings, ProcessingLog

logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 및 작업 관리자"""
    
    def __init__(self, database_path: Optional[str] = None):
        """
        데이터베이스 매니저 초기화
        
        Args:
            database_path: 데이터베이스 파일 경로 (None이면 기본 경로 사용)
        """
        if database_path is None:
            # 기본 데이터 디렉토리 생성
            data_dir = Path.home() / "SmartMailbox"
            data_dir.mkdir(exist_ok=True)
            database_path = str(data_dir / "mailbox.db")
        
        self.database_path = database_path
        self.engine = create_engine(
            f"sqlite:///{database_path}",
            echo=False,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False}
        )
        
        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # 테이블 생성
        Base.metadata.create_all(bind=self.engine)
        
        # 기본 태그 초기화
        self._initialize_default_tags()
        
        logger.info(f"데이터베이스 초기화 완료: {database_path}")
    
    @contextmanager
    def get_session(self):
        """데이터베이스 세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def _initialize_default_tags(self):
        """기본 시스템 태그 초기화"""
        default_tags = [
            {
                "name": "important",
                "display_name": "🔴 중요",
                "description": "긴급하거나 중요한 내용의 이메일",
                "color": "#FF4444",
                "icon": "priority_high",
                "is_system": True,
                "ai_prompt": "이 이메일이 중요하거나 긴급한 내용인지 판단해주세요.",
                "ai_keywords": '["urgent", "important", "asap", "긴급", "중요"]'
            },
            {
                "name": "reply_needed",
                "display_name": "💬 회신필요",
                "description": "답장이 필요한 이메일",
                "color": "#4A90E2",
                "icon": "reply",
                "is_system": True,
                "ai_prompt": "이 이메일에 회신이 필요한지 판단해주세요.",
                "ai_keywords": '["question", "request", "please", "질문", "요청"]'
            },
            {
                "name": "spam",
                "display_name": "🚫 스팸",
                "description": "스팸으로 분류된 이메일",
                "color": "#FF6B6B",
                "icon": "block",
                "is_system": True,
                "ai_prompt": "이 이메일이 스팸인지 판단해주세요.",
                "ai_keywords": '["spam", "phishing", "스팸", "피싱"]'
            },
            {
                "name": "advertisement",
                "display_name": "📢 광고",
                "description": "마케팅/광고 이메일",
                "color": "#FFA500",
                "icon": "campaign",
                "is_system": True,
                "ai_prompt": "이 이메일이 광고나 마케팅 목적인지 판단해주세요.",
                "ai_keywords": '["sale", "discount", "할인", "광고"]'
            }
        ]
        
        with self.get_session() as session:
            for tag_data in default_tags:
                existing_tag = session.query(Tag).filter_by(name=tag_data["name"]).first()
                if not existing_tag:
                    tag = Tag(**tag_data)
                    session.add(tag)
                    logger.info(f"기본 태그 생성: {tag_data['display_name']}")
    
    # 이메일 관련 CRUD 작업
    def save_email(self, email_data: Dict[str, Any]) -> int:
        """이메일 저장 후 ID 반환"""
        with self.get_session() as session:
            email = Email(**email_data)
            session.add(email)
            session.flush()
            return getattr(email, 'id')
    
    def get_email_by_id(self, email_id: int) -> Optional[Email]:
        """ID로 이메일 조회"""
        with self.get_session() as session:
            return session.query(Email).filter_by(id=email_id).first()
    
    def get_emails_by_tag(self, tag_name: str) -> List[Email]:
        """태그로 이메일 목록 조회"""
        with self.get_session() as session:
            return session.query(Email).join(Email.tags).filter(Tag.name == tag_name).all()
    
    def get_all_emails(self, limit: int = 100, offset: int = 0) -> List[Email]:
        """모든 이메일 조회 (페이징)"""
        with self.get_session() as session:
            return session.query(Email).order_by(Email.date_received.desc()).limit(limit).offset(offset).all()
    
    def search_emails(self, query: str) -> List[Email]:
        """이메일 검색"""
        with self.get_session() as session:
            search_filter = f"%{query}%"
            return session.query(Email).filter(
                (Email.subject.like(search_filter)) |
                (Email.sender.like(search_filter)) |
                (Email.body_text.like(search_filter))
            ).all()
    
    # 태그 관련 CRUD 작업
    def get_all_tags(self) -> List[Tag]:
        """모든 활성 태그 조회"""
        with self.get_session() as session:
            return session.query(Tag).filter(Tag.is_active == True).order_by(Tag.is_system.desc(), Tag.name).all()
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """이름으로 태그 조회"""
        with self.get_session() as session:
            return session.query(Tag).filter_by(name=name).first()
    
    def create_custom_tag(self, tag_data: Dict[str, Any]) -> int:
        """커스텀 태그 생성 후 ID 반환"""
        with self.get_session() as session:
            tag = Tag(**tag_data)
            session.add(tag)
            session.flush()
            return getattr(tag, 'id')
    
    def assign_tags_to_email(self, email_id: int, tag_names: List[str]):
        """이메일에 태그 할당"""
        with self.get_session() as session:
            email = session.query(Email).filter_by(id=email_id).first()
            if not email:
                raise ValueError(f"Email with ID {email_id} not found")
            
            # 기존 태그 초기화
            email.tags.clear()
            
            # 새 태그 할당
            for tag_name in tag_names:
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if tag:
                    email.tags.append(tag)
            
            # AI 처리 완료 표시
            session.execute(
                update(Email).where(Email.id == email_id).values(
                    ai_processed=True,
                    ai_processing_date=datetime.utcnow()
                )
            )
    
    # 설정 관련 작업
    def get_setting(self, key: str, default: Any = None) -> Any:
        """설정 값 조회"""
        with self.get_session() as session:
            setting = session.query(AppSettings).filter_by(key=key).first()
            if setting and setting.value is not None:
                try:
                    # 타입에 따라 변환
                    value_type = getattr(setting, 'value_type')
                    value = getattr(setting, 'value')
                    if value_type == "int":
                        return int(value)
                    elif value_type == "float":
                        return float(value)
                    elif value_type == "bool":
                        return value.lower() == "true"
                    elif value_type == "json":
                        import json
                        return json.loads(value)
                    else:
                        return value
                except (ValueError, TypeError):
                    logger.warning(f"설정 값 변환 실패: {key}")
                    return default
            return default
    
    def set_setting(self, key: str, value: Any, description: Optional[str] = None):
        """설정 값 저장"""
        with self.get_session() as session:
            setting = session.query(AppSettings).filter_by(key=key).first()
            
            # 값 타입 판단 및 문자열 변환
            if isinstance(value, bool):
                value_type = "bool"
                value_str = str(value).lower()
            elif isinstance(value, int):
                value_type = "int"
                value_str = str(value)
            elif isinstance(value, float):
                value_type = "float"
                value_str = str(value)
            elif isinstance(value, (dict, list)):
                value_type = "json"
                import json
                value_str = json.dumps(value)
            else:
                value_type = "string"
                value_str = str(value)
            
            if setting:
                setattr(setting, 'value', value_str)
                setattr(setting, 'value_type', value_type)
                if description:
                    setattr(setting, 'description', description)
                setattr(setting, 'updated_at', datetime.utcnow())
            else:
                setting = AppSettings(
                    key=key,
                    value=value_str,
                    value_type=value_type,
                    description=description
                )
                session.add(setting)
    
    # 로그 관련 작업
    def log_processing(self, operation_type: str, operation_status: str, 
                      message: Optional[str] = None, email_id: Optional[int] = None, 
                      error_details: Optional[str] = None, processing_time_ms: Optional[int] = None):
        """처리 로그 저장"""
        with self.get_session() as session:
            log = ProcessingLog(
                email_id=email_id,
                operation_type=operation_type,
                operation_status=operation_status,
                message=message,
                error_details=error_details,
                processing_time_ms=processing_time_ms
            )
            session.add(log)
    
    def get_processing_logs(self, limit: int = 100) -> List[ProcessingLog]:
        """처리 로그 조회"""
        with self.get_session() as session:
            return session.query(ProcessingLog).order_by(ProcessingLog.created_at.desc()).limit(limit).all()
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결 종료") 