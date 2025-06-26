"""
데이터베이스 연결 및 관리
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, update, or_
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Email, Tag, AppSettings, ProcessingLog

logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 및 작업 관리자"""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
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
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self._initialize_default_tags()
        logger.info(f"데이터베이스 초기화 완료: {database_path}")
    
    @contextmanager
    def get_session(self):
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
        default_tags = [
            {"name": "important", "display_name": "🔴 중요", "description": "긴급하거나 중요한 내용의 이메일", "color": "#FF4444", "is_system": True, "ai_prompt": "이 이메일이 중요하거나 긴급한 내용인지 판단해주세요."},
            {"name": "reply_needed", "display_name": "💬 회신필요", "description": "답장이 필요한 이메일", "color": "#4A90E2", "is_system": True, "ai_prompt": "이 이메일에 회신이 필요한지 판단해주세요."},
            {"name": "spam", "display_name": "🚫 스팸", "description": "스팸으로 분류된 이메일", "color": "#FF6B6B", "is_system": True, "ai_prompt": "이 이메일이 스팸인지 판단해주세요."},
            {"name": "advertisement", "display_name": "📢 광고", "description": "마케팅/광고 이메일", "color": "#FFA500", "is_system": True, "ai_prompt": "이 이메일이 광고나 마케팅 목적인지 판단해주세요."}
        ]
        with self.get_session() as session:
            for tag_data in default_tags:
                existing_tag = session.query(Tag).filter_by(name=tag_data["name"]).first()
                if not existing_tag:
                    session.add(Tag(**tag_data))

    def get_emails(
        self,
        search_query: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "date_desc",
        limit: int = 100,
        offset: int = 0
    ) -> List[Email]:
        """
        다양한 조건으로 이메일을 검색하고 필터링합니다.
        """
        with self.get_session() as session:
            query: Query = session.query(Email)

            if search_query:
                search_filter = f"%{search_query}%"
                query = query.filter(
                    or_(
                        Email.subject.like(search_filter),
                        Email.sender.like(search_filter),
                        Email.body_text.like(search_filter)
                    )
                )

            if tag_names:
                query = query.join(Email.tags).filter(Tag.name.in_(tag_names))

            if date_from:
                query = query.filter(Email.date_received >= date_from)
            
            if date_to:
                query = query.filter(Email.date_received <= date_to)

            # 정렬
            if sort_by == "date_desc":
                query = query.order_by(Email.date_received.desc())
            elif sort_by == "date_asc":
                query = query.order_by(Email.date_received.asc())
            elif sort_by == "sender_asc":
                query = query.order_by(Email.sender.asc())
            
            return query.limit(limit).offset(offset).all()

    def save_email(self, email_data: Dict[str, Any]) -> int:
        with self.get_session() as session:
            email = Email(**email_data)
            session.add(email)
            session.flush()
            return getattr(email, 'id')
    
    def get_email_by_id(self, email_id: int) -> Optional[Email]:
        with self.get_session() as session:
            return session.query(Email).filter_by(id=email_id).first()
    
    def get_all_tags(self) -> List[Tag]:
        with self.get_session() as session:
            return session.query(Tag).filter(Tag.is_active == True).order_by(Tag.is_system.desc(), Tag.name).all()

    def assign_tags_to_email(self, email_id: int, tag_names: List[str]):
        with self.get_session() as session:
            email = session.query(Email).filter_by(id=email_id).first()
            if not email:
                raise ValueError(f"Email with ID {email_id} not found")
            
            email.tags.clear()
            
            for tag_name in tag_names:
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if tag:
                    email.tags.append(tag)
            
            session.execute(
                update(Email).where(Email.id == email_id).values(
                    ai_processed=True,
                    ai_processing_date=datetime.utcnow()
                )
            )

    def close(self):
        if self.engine:
            self.engine.dispose()
            logger.info("데이터베이스 연결 종료") 