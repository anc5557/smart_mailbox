"""
이메일 자동 태깅 매니저
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from .ollama_client import OllamaClient, OllamaConfig, EmailTagger
from ..storage.database import DatabaseManager
from ..storage.models import Email

logger = logging.getLogger(__name__)


class EmailTaggingManager:
    """이메일 자동 태깅 매니저"""
    
    def __init__(self, database_manager: DatabaseManager, ollama_config: Optional[OllamaConfig] = None):
        self.db = database_manager
        self.ollama_client = OllamaClient(ollama_config)
        self.email_tagger = EmailTagger(self.ollama_client)
        
    def is_ai_available(self) -> bool:
        """AI 서비스 사용 가능 여부 확인"""
        return self.ollama_client.is_available()
    
    def process_email(self, email_id: int) -> Dict[str, Any]:
        """
        이메일 처리 및 자동 태깅
        
        Args:
            email_id: 처리할 이메일 ID
            
        Returns:
            처리 결과 정보
        """
        start_time = time.time()
        
        try:
            # 이메일 데이터 조회
            email = self.db.get_email_by_id(email_id)
            if not email:
                raise ValueError(f"Email with ID {email_id} not found")
            
            # 이미 처리된 이메일인지 확인
            if getattr(email, 'ai_processed', False):
                logger.info(f"이메일 {email_id}는 이미 처리되었습니다.")
                return {
                    "email_id": email_id,
                    "status": "already_processed",
                    "tags": [tag.name for tag in email.tags],
                    "processing_time": 0
                }
            
            # AI 서비스 가용성 확인
            if not self.is_ai_available():
                logger.error("AI 서비스를 사용할 수 없습니다.")
                self.db.log_processing(
                    operation_type="ai_tag",
                    operation_status="error",
                    message="AI 서비스 사용 불가",
                    email_id=email_id
                )
                return {
                    "email_id": email_id,
                    "status": "ai_unavailable",
                    "error": "AI 서비스에 연결할 수 없습니다."
                }
            
            # 이메일 데이터 변환
            email_data = self._email_to_dict(email)
            
            # 태그 설정 조회
            tags_config = self._get_tags_config()
            
            # AI 태깅 수행
            logger.info(f"이메일 {email_id} AI 태깅 시작")
            classification_result = self.email_tagger.classify_email(email_data, tags_config)
            
            # 태그 할당
            if classification_result["tags"]:
                self.db.assign_tags_to_email(email_id, classification_result["tags"])
                logger.info(f"이메일 {email_id}에 태그 할당 완료: {classification_result['tags']}")
            
            # 신뢰도 점수 업데이트
            processing_time = int((time.time() - start_time) * 1000)
            
            # 처리 로그 저장
            self.db.log_processing(
                operation_type="ai_tag",
                operation_status="success",
                message=f"태그 할당 완료: {', '.join(classification_result['tags'])}",
                email_id=email_id,
                processing_time_ms=processing_time
            )
            
            return {
                "email_id": email_id,
                "status": "success",
                "tags": classification_result["tags"],
                "confidence_scores": classification_result["confidence_scores"],
                "overall_confidence": classification_result["overall_confidence"],
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"이메일 {email_id} 태깅 실패: {e}")
            
            # 오류 로그 저장
            self.db.log_processing(
                operation_type="ai_tag",
                operation_status="error",
                message="태깅 처리 실패",
                email_id=email_id,
                error_details=str(e),
                processing_time_ms=processing_time
            )
            
            return {
                "email_id": email_id,
                "status": "error",
                "error": str(e),
                "processing_time": processing_time
            }
    
    def process_multiple_emails(self, email_ids: List[int]) -> List[Dict[str, Any]]:
        """여러 이메일 일괄 처리"""
        results = []
        
        for email_id in email_ids:
            result = self.process_email(email_id)
            results.append(result)
            
            # 처리 간격 (서버 부하 방지)
            time.sleep(0.5)
        
        return results
    
    def reprocess_email(self, email_id: int, force: bool = False) -> Dict[str, Any]:
        """이메일 재처리"""
        if force:
            # 강제 재처리를 위해 AI 처리 상태 초기화
            with self.db.get_session() as session:
                email = session.query(Email).filter_by(id=email_id).first()
                if email:
                    setattr(email, 'ai_processed', False)
                    email.tags.clear()
        
        return self.process_email(email_id)
    
    def get_unprocessed_emails(self, limit: int = 50) -> List[int]:
        """미처리 이메일 ID 목록 조회"""
        try:
            with self.db.get_session() as session:
                emails = session.query(Email).filter_by(ai_processed=False).limit(limit).all()
                return [getattr(email, 'id') for email in emails]
        except Exception as e:
            logger.error(f"미처리 이메일 조회 실패: {e}")
            return []
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """처리 통계 조회"""
        try:
            with self.db.get_session() as session:
                total_emails = session.query(Email).count()
                processed_emails = session.query(Email).filter_by(ai_processed=True).count()
                unprocessed_emails = total_emails - processed_emails
                
                # 태그별 통계
                tag_stats = {}
                tags = self.db.get_all_tags()
                for tag in tags:
                    count = len(self.db.get_emails_by_tag(getattr(tag, 'name')))
                    tag_stats[getattr(tag, 'display_name')] = count
                
                return {
                    "total_emails": total_emails,
                    "processed_emails": processed_emails,
                    "unprocessed_emails": unprocessed_emails,
                    "processing_rate": processed_emails / total_emails if total_emails > 0 else 0,
                    "tag_statistics": tag_stats
                }
                
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def _email_to_dict(self, email) -> Dict[str, Any]:
        """이메일 ORM 객체를 딕셔너리로 변환"""
        return {
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "sender_name": email.sender_name,
            "recipient": email.recipient,
            "recipient_name": email.recipient_name,
            "body_text": email.body_text,
            "body_html": email.body_html,
            "date_sent": email.date_sent,
            "has_attachments": email.has_attachments,
            "attachment_count": email.attachment_count
        }
    
    def _get_tags_config(self) -> List[Dict[str, Any]]:
        """태그 설정 조회"""
        tags = self.db.get_all_tags()
        return [
            {
                "name": tag.name,
                "display_name": tag.display_name,
                "ai_prompt": tag.ai_prompt,
                "ai_keywords": tag.ai_keywords
            }
            for tag in tags
            if getattr(tag, 'ai_prompt', None)  # AI 프롬프트가 있는 태그만
        ]
    
    def close(self):
        """리소스 정리"""
        if self.ollama_client:
            self.ollama_client.close()


class BatchProcessor:
    """배치 처리기"""
    
    def __init__(self, tagging_manager: EmailTaggingManager):
        self.tagging_manager = tagging_manager
    
    def process_all_unprocessed(self, batch_size: int = 10) -> Dict[str, Any]:
        """모든 미처리 이메일 배치 처리"""
        logger.info("미처리 이메일 배치 처리 시작")
        
        total_processed = 0
        successful_processed = 0
        failed_processed = 0
        
        while True:
            # 미처리 이메일 조회
            unprocessed_ids = self.tagging_manager.get_unprocessed_emails(batch_size)
            
            if not unprocessed_ids:
                break
            
            logger.info(f"배치 처리 중: {len(unprocessed_ids)}개 이메일")
            
            # 배치 처리
            results = self.tagging_manager.process_multiple_emails(unprocessed_ids)
            
            # 결과 집계
            for result in results:
                total_processed += 1
                if result["status"] == "success":
                    successful_processed += 1
                else:
                    failed_processed += 1
            
            logger.info(f"배치 처리 완료: 성공 {successful_processed}, 실패 {failed_processed}")
        
        logger.info(f"배치 처리 완료: 총 {total_processed}개 처리됨")
        
        return {
            "total_processed": total_processed,
            "successful": successful_processed,
            "failed": failed_processed,
            "success_rate": successful_processed / total_processed if total_processed > 0 else 0
        } 