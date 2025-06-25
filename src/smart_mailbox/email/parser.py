"""
이메일 파일 파싱 모듈
"""

import email
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from email.message import EmailMessage, Message
from email.utils import parseaddr, parsedate_to_datetime
from email import header
import chardet

logger = logging.getLogger(__name__)


class EmailParser:
    """이메일 파일 파서"""
    
    def __init__(self):
        self.supported_extensions = {'.eml', '.msg'}
    
    def parse_eml_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        .eml 파일을 파싱하여 이메일 정보 추출
        
        Args:
            file_path: .eml 파일 경로
            
        Returns:
            파싱된 이메일 정보 딕셔너리
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않음
            ValueError: 파일 형식이 올바르지 않음
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        if file_path.suffix.lower() not in self.supported_extensions:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {file_path.suffix}")
        
        try:
            # 파일 읽기 (인코딩 자동 감지)
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            # 인코딩 감지 및 디코딩
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding') or 'utf-8'
            
            try:
                email_content = raw_data.decode(encoding)
            except UnicodeDecodeError:
                # 대체 인코딩 시도
                for fallback_encoding in ['utf-8', 'cp949', 'euc-kr', 'latin1']:
                    try:
                        email_content = raw_data.decode(fallback_encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    email_content = raw_data.decode('utf-8', errors='ignore')
            
            # 이메일 메시지 파싱
            message = email.message_from_string(email_content)
            
            # 기본 정보 추출
            email_data = self._extract_basic_info(message, file_path, len(raw_data))
            
            # 본문 추출
            body_text, body_html = self._extract_body(message)
            email_data['body_text'] = body_text
            email_data['body_html'] = body_html
            
            # 첨부파일 정보 추출
            attachment_info = self._extract_attachments(message)
            email_data['has_attachments'] = len(attachment_info) > 0
            email_data['attachment_count'] = len(attachment_info)
            email_data['attachment_info'] = str(attachment_info) if attachment_info else None
            
            # 파일 해시 계산
            email_data['file_hash'] = hashlib.sha256(raw_data).hexdigest()
            
            logger.info(f"이메일 파싱 완료: {file_path}")
            return email_data
            
        except Exception as e:
            logger.error(f"이메일 파싱 실패: {file_path} - {e}")
            raise ValueError(f"이메일 파싱 중 오류 발생: {e}")
    
    def _extract_basic_info(self, message: Message, file_path: Path, file_size: int) -> Dict[str, Any]:
        """기본 이메일 정보 추출"""
        
        # 제목 처리
        subject = self._decode_header(message.get('Subject', '제목 없음'))
        
        # 발신자 정보 처리
        from_header = message.get('From', '')
        sender_name, sender_email = parseaddr(from_header)
        sender_email = sender_email if sender_email else from_header
        sender_name = self._decode_header(sender_name) if sender_name else None
        
        # 수신자 정보 처리
        to_header = message.get('To', '')
        recipient_name, recipient_email = parseaddr(to_header)
        recipient_email = recipient_email if recipient_email else to_header
        recipient_name = self._decode_header(recipient_name) if recipient_name else None
        
        # 날짜 처리
        date_header = message.get('Date')
        if date_header:
            try:
                date_sent = parsedate_to_datetime(date_header)
                # UTC로 변환
                if date_sent.tzinfo is None:
                    date_sent = date_sent.replace(tzinfo=None)
                else:
                    date_sent = date_sent.utctimetuple()
                    date_sent = datetime(*date_sent[:6])
            except (ValueError, TypeError):
                date_sent = datetime.utcnow()
        else:
            date_sent = datetime.utcnow()
        
        return {
            'subject': subject,
            'sender': sender_email,
            'sender_name': sender_name,
            'recipient': recipient_email,
            'recipient_name': recipient_name,
            'date_sent': date_sent,
            'date_received': datetime.utcnow(),
            'file_path': str(file_path.absolute()),
            'file_size': file_size,
            'ai_processed': False
        }
    
    def _extract_body(self, message: Message) -> Tuple[Optional[str], Optional[str]]:
        """이메일 본문 추출 (텍스트 및 HTML)"""
        body_text = None
        body_html = None
        
        if message.is_multipart():
            # 멀티파트 메시지 처리
            for part in message.walk():
                content_type = part.get_content_type()
                
                if content_type == 'text/plain' and not body_text:
                    body_text = self._get_payload_text(part)
                elif content_type == 'text/html' and not body_html:
                    body_html = self._get_payload_text(part)
        else:
            # 단일 파트 메시지 처리
            content_type = message.get_content_type()
            
            if content_type == 'text/plain':
                body_text = self._get_payload_text(message)
            elif content_type == 'text/html':
                body_html = self._get_payload_text(message)
            else:
                # 기본적으로 텍스트로 처리
                body_text = self._get_payload_text(message)
        
        return body_text, body_html
    
    def _get_payload_text(self, part: Message) -> Optional[str]:
        """메시지 파트에서 텍스트 추출"""
        try:
            payload = part.get_payload(decode=True)
            if payload:
                # 인코딩 감지 및 디코딩
                if isinstance(payload, bytes):
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        return payload.decode(charset)
                    except (UnicodeDecodeError, LookupError):
                        # 대체 인코딩 시도
                        for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin1']:
                            try:
                                return payload.decode(encoding)
                            except (UnicodeDecodeError, LookupError):
                                continue
                        return payload.decode('utf-8', errors='ignore')
                else:
                    return str(payload)
        except Exception as e:
            logger.warning(f"페이로드 추출 실패: {e}")
        
        return None
    
    def _extract_attachments(self, message: Message) -> List[Dict[str, Any]]:
        """첨부파일 정보 추출"""
        attachments = []
        
        if message.is_multipart():
            for part in message.walk():
                content_disposition = part.get('Content-Disposition', '')
                
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        
                        attachment_info = {
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b'')
                        }
                        attachments.append(attachment_info)
        
        return attachments
    
    def _decode_header(self, header_value: str) -> str:
        """헤더 값 디코딩 (MIME 인코딩 포함)"""
        if not header_value:
            return ""
        
        try:
            decoded_parts = header.decode_header(header_value)
            decoded_text = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_text += part.decode(encoding, errors='ignore')
                    else:
                        # 인코딩이 명시되지 않은 경우 추측
                        try:
                            decoded_text += part.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                decoded_text += part.decode('cp949')
                            except UnicodeDecodeError:
                                decoded_text += part.decode('utf-8', errors='ignore')
                else:
                    decoded_text += str(part)
            
            return decoded_text.strip()
            
        except Exception as e:
            logger.warning(f"헤더 디코딩 실패: {header_value} - {e}")
            return str(header_value)
    
    def validate_email_file(self, file_path: Union[str, Path]) -> bool:
        """이메일 파일 유효성 검사"""
        try:
            file_path = Path(file_path)
            
            # 파일 존재 여부 확인
            if not file_path.exists():
                return False
            
            # 파일 확장자 확인
            if file_path.suffix.lower() not in self.supported_extensions:
                return False
            
            # 파일 크기 확인 (너무 크면 제외)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_path.stat().st_size > max_size:
                logger.warning(f"파일이 너무 큽니다: {file_path}")
                return False
            
            # 기본적인 이메일 구조 확인
            with open(file_path, 'rb') as f:
                sample = f.read(1024).decode('utf-8', errors='ignore')
            
            # 이메일 헤더 패턴 확인
            email_patterns = ['From:', 'To:', 'Subject:', 'Date:', 'Message-ID:']
            found_patterns = sum(1 for pattern in email_patterns if pattern in sample)
            
            return found_patterns >= 2  # 최소 2개의 헤더가 있어야 함
            
        except Exception as e:
            logger.error(f"파일 유효성 검사 실패: {file_path} - {e}")
            return False


# 편의 함수들
def parse_email_file(file_path: str) -> Dict[str, Any]:
    """이메일 파일 파싱 편의 함수"""
    parser = EmailParser()
    return parser.parse_eml_file(file_path)


def is_valid_email_file(file_path: str) -> bool:
    """이메일 파일 유효성 검사 편의 함수"""
    parser = EmailParser()
    return parser.validate_email_file(file_path) 