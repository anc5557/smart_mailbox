"""
데이터베이스 모델 정의
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, Table, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# 이메일과 태그 간의 다대다 관계 테이블
email_tags = Table(
    'email_tags',
    Base.metadata,
    Column('email_id', Integer, ForeignKey('emails.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class Email(Base):
    """이메일 정보 모델"""
    __tablename__ = 'emails'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 이메일 메타데이터
    subject = Column(String(500), nullable=False)
    sender = Column(String(200), nullable=False)
    sender_name = Column(String(200))
    recipient = Column(String(200), nullable=False)
    recipient_name = Column(String(200))
    date_sent = Column(DateTime, nullable=False)
    date_received = Column(DateTime, default=datetime.utcnow)
    
    # 이메일 내용
    body_text = Column(Text)
    body_html = Column(Text)
    
    # 파일 정보
    file_path = Column(String(500), nullable=False)  # 원본 .eml 파일 경로
    file_size = Column(Integer)
    file_hash = Column(String(64))  # SHA-256 해시
    
    # AI 분석 결과
    ai_processed = Column(Boolean, default=False)
    ai_processing_date = Column(DateTime)
    ai_confidence_score = Column(Float)  # 태깅 신뢰도 점수
    
    # 첨부파일 정보
    has_attachments = Column(Boolean, default=False)
    attachment_count = Column(Integer, default=0)
    attachment_info = Column(Text)  # JSON 형태로 첨부파일 정보 저장
    
    # 관계 설정
    tags = relationship("Tag", secondary=email_tags, back_populates="emails")
    
    def __repr__(self):
        return f"<Email(id={self.id}, subject='{self.subject[:50]}...', sender='{self.sender}')>"


class Tag(Base):
    """태그 정보 모델"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 태그 기본 정보
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 태그 스타일
    color = Column(String(7), default="#007ACC")  # 헥사 컬러 코드
    icon = Column(String(50))  # 아이콘 이름
    
    # 태그 타입
    is_system = Column(Boolean, default=False)  # 시스템 기본 태그 여부
    is_active = Column(Boolean, default=True)
    
    # AI 분류용 프롬프트
    ai_prompt = Column(Text)
    ai_keywords = Column(Text)  # JSON 배열 형태의 키워드
    
    # 생성/수정 시간
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    emails = relationship("Email", secondary=email_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class AppSettings(Base):
    """애플리케이션 설정 모델"""
    __tablename__ = 'app_settings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 설정 키-값
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, int, float, bool, json
    
    # 설정 메타데이터
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AppSettings(key='{self.key}', value_type='{self.value_type}')>"


class ProcessingLog(Base):
    """처리 로그 모델 (디버깅 및 모니터링용)"""
    __tablename__ = 'processing_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 로그 정보
    email_id = Column(Integer, ForeignKey('emails.id'), nullable=True)
    operation_type = Column(String(50), nullable=False)  # 'email_parse', 'ai_tag', 'ai_reply' 등
    operation_status = Column(String(20), nullable=False)  # 'success', 'error', 'warning'
    
    # 상세 정보
    message = Column(Text)
    error_details = Column(Text)
    processing_time_ms = Column(Integer)  # 처리 시간 (밀리초)
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ProcessingLog(operation='{self.operation_type}', status='{self.operation_status}')>" 