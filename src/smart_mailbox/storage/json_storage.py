"""
JSON 파일 기반 데이터 저장소 관리
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Email:
    """이메일 정보 데이터 클래스"""
    id: str
    subject: str
    sender: str
    sender_name: Optional[str] = None
    recipient: str = ""
    recipient_name: Optional[str] = None
    date_sent: str = ""
    date_received: str = ""
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    file_path: str = ""
    file_size: int = 0
    file_hash: Optional[str] = None
    ai_processed: bool = False
    ai_processing_date: Optional[str] = None
    ai_confidence_score: Optional[float] = None
    has_attachments: bool = False
    attachment_count: int = 0
    attachment_info: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Email':
        return cls(**data)


@dataclass
class Tag:
    """태그 정보 데이터 클래스"""
    id: str
    name: str
    display_name: str
    description: str = ""
    color: str = "#007ACC"
    icon: Optional[str] = None
    is_system: bool = False
    is_active: bool = True
    ai_prompt: Optional[str] = None
    ai_keywords: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tag':
        return cls(**data)


@dataclass
class AppSetting:
    """애플리케이션 설정 데이터 클래스"""
    key: str
    value: Any
    value_type: str = "string"
    description: str = ""
    is_encrypted: bool = False
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSetting':
        return cls(**data)


@dataclass
class ProcessingLog:
    """처리 로그 데이터 클래스"""
    id: str
    email_id: Optional[str] = None
    operation_type: str = ""
    operation_status: str = ""
    message: Optional[str] = None
    error_details: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingLog':
        return cls(**data)


class JSONStorageManager:
    """JSON 파일 기반 데이터 저장소 관리자"""
    
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir_path = Path.home() / "SmartMailbox"
        else:
            data_dir_path = Path(data_dir)
        
        self.data_dir = data_dir_path
        self.data_dir.mkdir(exist_ok=True)
        
        # JSON 파일 경로 설정
        self.emails_file = self.data_dir / "emails.json"
        self.tags_file = self.data_dir / "tags.json"
        self.settings_file = self.data_dir / "settings.json"
        self.logs_file = self.data_dir / "logs.json"
        
        # 데이터 초기화
        self._initialize_files()
        self._initialize_default_tags()
        
        logger.info(f"JSON 데이터 저장소 초기화 완료: {self.data_dir}")
    
    def _initialize_files(self):
        """JSON 파일들을 초기화합니다."""
        if not self.emails_file.exists():
            self._save_json(self.emails_file, [])
        
        if not self.tags_file.exists():
            self._save_json(self.tags_file, [])
        
        if not self.settings_file.exists():
            self._save_json(self.settings_file, [])
        
        if not self.logs_file.exists():
            self._save_json(self.logs_file, [])
    
    def _load_json(self, file_path: Path) -> Any:
        """JSON 파일을 로드합니다."""
        try:
            if not file_path.exists():
                logger.info(f"JSON 파일이 존재하지 않음 {file_path}, 빈 배열로 초기화")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.info(f"JSON 파일이 비어있음 {file_path}, 빈 배열로 초기화")
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파일 파싱 실패 {file_path}: {e}")
            # 백업 파일로 복사 후 초기화
            backup_path = file_path.with_suffix('.json.backup')
            try:
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"손상된 파일을 {backup_path}로 백업함")
            except Exception:
                pass
            return []
        except Exception as e:
            logger.error(f"JSON 파일 로드 실패 {file_path}: {e}")
            return []
    
    def _save_json(self, file_path: Path, data: Any):
        """JSON 파일을 저장합니다."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=self._json_serializer)
        except Exception as e:
            logger.error(f"JSON 파일 저장 실패 {file_path}: {e}")
            raise
    
    def _json_serializer(self, obj):
        """JSON 직렬화를 위한 커스텀 시리얼라이저"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def _initialize_default_tags(self):
        """기본 태그들을 초기화합니다."""
        default_tags = [
            {
                "id": "중요",
                "name": "중요",
                "display_name": "🔴 중요",
                "description": "긴급하거나 중요한 내용의 이메일",
                "color": "#FF4444",
                "is_system": True,
                "is_active": True,
                "ai_prompt": """다음 기준 중 하나 이상에 해당하면 중요 태그를 적용하세요:

1. **긴급성 표현**: "긴급", "urgent", "ASAP", "즉시", "오늘까지", "deadline" 등의 표현
2. **중요도 표현**: "중요", "important", "critical", "필수", "반드시" 등의 표현  
3. **상사/고객/중요 인물**: 회사 임원, 주요 고객, VIP 등으로부터의 이메일
4. **업무 중요 사안**: 프로젝트 마감, 계약 관련, 법적 사안, 보안 문제 등
5. **결정 요구**: 승인, 결재, 중요한 의사결정이 필요한 사안
6. **시간 제약**: 특정 시간까지 응답이나 처리가 필요한 사안

제목이나 내용에서 위 요소들이 명확히 드러나는 경우에만 적용하세요.""",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "회신필요",
                "name": "회신필요",
                "display_name": "💬 회신필요",
                "description": "답장이 필요한 이메일",
                "color": "#4A90E2",
                "is_system": True,
                "is_active": True,
                "ai_prompt": """다음 기준에 해당하면 회신필요 태그를 적용하세요:

1. **직접적 질문**: 구체적인 질문이 포함되어 있는 경우
2. **응답 요청**: "답장 주세요", "회신 바랍니다", "알려주세요" 등의 명시적 요청
3. **확인 요청**: 일정, 참석, 승인 등에 대한 확인을 요구하는 경우  
4. **회의/미팅 관련**: 회의 일정 조율, 참석 여부 확인 등
5. **정보 요청**: 문서, 자료, 정보 제공을 요구하는 경우
6. **피드백 요청**: 의견, 검토, 평가를 요구하는 경우

단순 정보 전달이나 일방적 알림은 제외하세요.""",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "스팸",
                "name": "스팸",
                "display_name": "🚫 스팸",
                "description": "스팸으로 분류된 이메일",
                "color": "#FF6B6B",
                "is_system": True,
                "is_active": True,
                "ai_prompt": """다음 기준에 해당하면 스팸 태그를 적용하세요:

1. **의심스러운 발신자**: 알 수 없는 이메일 주소, 랜덤한 문자열 조합
2. **스팸 특징적 제목**: "광고", "혜택", "무료", "당첨", "긴급", 과도한 특수문자
3. **피싱 의심**: 개인정보, 비밀번호, 카드정보 요구
4. **과도한 링크**: 의심스러운 링크나 첨부파일이 다수 포함
5. **문법/맞춤법 오류**: 부자연스러운 한국어나 번역체 문장
6. **금전 관련 사기**: 투자, 대출, 상금, 환급 등 금전적 유혹

신뢰할 수 있는 기업이나 개인으로부터의 이메일은 제외하세요.""",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "광고",
                "name": "광고",
                "display_name": "📢 광고",
                "description": "마케팅/광고 이메일",
                "color": "#FFA500",
                "is_system": True,
                "is_active": True,
                "ai_prompt": """다음 기준에 해당하면 광고 태그를 적용하세요:

1. **상업적 홍보**: 제품, 서비스, 브랜드를 홍보하는 내용
2. **마케팅 용어**: "할인", "특가", "이벤트", "프로모션", "세일" 등
3. **뉴스레터**: 회사 소식, 업계 동향 등을 정기적으로 전달하는 이메일
4. **구매 유도**: 구매 링크, 쿠폰, 혜택 안내 등이 포함된 경우
5. **구독 서비스**: 정기 구독 서비스의 홍보나 안내 메일
6. **마케팅 템플릿**: 전형적인 마케팅 이메일 형식과 디자인

개인적인 추천이나 업무 관련 제품 소개는 제외하세요.""",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        existing_tags = self._load_json(self.tags_file)
        if not existing_tags:
            self._save_json(self.tags_file, default_tags)
    
    def sync_tags_with_config(self, tag_config):
        """TagConfig의 태그들을 JSON과 동기화합니다."""
        existing_tags = self._load_json(self.tags_file)
        
        # 기존 태그가 배열 형태인지 확인하고 딕셔너리로 변환
        if isinstance(existing_tags, list):
            existing_tag_names = {tag.get('name') for tag in existing_tags if isinstance(tag, dict)}
        else:
            # TagConfig 스타일이라면 기본 태그로 재생성
            self._initialize_default_tags()
            existing_tags = self._load_json(self.tags_file)
            existing_tag_names = {tag.get('name') for tag in existing_tags if isinstance(tag, dict)}
        
        config_tags = tag_config.get_all_tags()
        new_tags = []
        
        for korean_name, tag_info in config_tags.items():
            if korean_name not in existing_tag_names:
                is_system = korean_name in ["중요", "회신필요", "스팸", "광고"]
                new_tag = {
                    "id": korean_name,
                    "name": korean_name,
                    "display_name": self._get_system_display_name(korean_name) if is_system else korean_name,
                    "description": tag_info.get('description', ''),
                    "color": tag_info.get('color', '#007ACC'),
                    "is_system": is_system,
                    "ai_prompt": tag_info.get('prompt', ''),
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                new_tags.append(new_tag)
                existing_tags.append(new_tag)
                print(f"새 태그 추가: {korean_name}")
        
        if new_tags:
            self._save_json(self.tags_file, existing_tags)
    
    def _get_system_display_name(self, korean_name):
        """시스템 태그의 표시명을 반환합니다."""
        system_display_names = {
            "중요": "🔴 중요",
            "회신필요": "💬 회신필요",
            "스팸": "🚫 스팸",
            "광고": "📢 광고"
        }
        return system_display_names.get(korean_name, korean_name)
    
    def create_custom_tag(self, name: str, display_name: str, color: str, prompt: str, description: str = "") -> bool:
        """커스텀 태그를 생성합니다."""
        try:
            tags = self._load_json(self.tags_file)
            
            # 중복 확인
            for tag in tags:
                if tag.get('name') == name:
                    return False
            
            new_tag = {
                "id": str(uuid4()),
                "name": name,
                "display_name": display_name,
                "description": description,
                "color": color,
                "ai_prompt": prompt,
                "is_system": False,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            tags.append(new_tag)
            self._save_json(self.tags_file, tags)
            return True
        except Exception as e:
            logger.error(f"커스텀 태그 생성 실패: {e}")
            return False
    
    def get_tag_prompts_for_ai(self) -> Dict[str, str]:
        """AI 태깅을 위한 태그별 프롬프트를 반환합니다."""
        tags = self._load_json(self.tags_file)
        result = {}
        
        # 태그가 배열 형태인지 확인
        if isinstance(tags, list):
            for tag in tags:
                # 각 태그가 딕셔너리인지 확인
                if isinstance(tag, dict):
                    if tag.get('is_active', True) and tag.get('ai_prompt'):
                        result[tag['name']] = tag['ai_prompt']
        elif isinstance(tags, dict):
            # TagConfig 딕셔너리 형태인 경우
            for korean_name, tag_info in tags.items():
                if isinstance(tag_info, dict) and tag_info.get('prompt'):
                    result[korean_name] = tag_info['prompt']
        
        return result
    
    def get_emails(
        self,
        search_query: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "date_desc",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """다양한 조건으로 이메일을 검색하고 필터링합니다."""
        emails = self._load_json(self.emails_file)
        
        # 검색 쿼리 필터링 - 더 포괄적인 검색
        if search_query:
            search_query = search_query.lower()
            filtered_emails = []
            
            for email in emails:
                # 검색 대상 필드들
                search_fields = [
                    email.get('subject', ''),
                    email.get('sender', ''),
                    email.get('sender_name', '') or '',
                    email.get('recipient', ''),
                    email.get('recipient_name', '') or '',
                    email.get('body_text', '') or '',
                ]
                
                # 태그도 검색 대상에 포함
                email_tags = email.get('tags', [])
                if email_tags:
                    if isinstance(email_tags, list):
                        search_fields.extend(email_tags)
                
                # 모든 필드를 하나의 문자열로 합치고 검색
                combined_text = ' '.join(str(field) for field in search_fields).lower()
                
                if search_query in combined_text:
                    filtered_emails.append(email)
            
            emails = filtered_emails
        
        # 태그 필터링
        if tag_names:
            emails = [
                email for email in emails
                if any(tag in email.get('tags', []) for tag in tag_names)
            ]
        
        # 날짜 필터링
        if date_from:
            emails = [
                email for email in emails
                if email.get('date_received') and 
                datetime.fromisoformat(email['date_received'].replace('Z', '+00:00')) >= date_from
            ]
        
        if date_to:
            emails = [
                email for email in emails
                if email.get('date_received') and 
                datetime.fromisoformat(email['date_received'].replace('Z', '+00:00')) <= date_to
            ]
        
        # 정렬
        if sort_by == "date_desc":
            emails.sort(key=lambda x: x.get('date_received', ''), reverse=True)
        elif sort_by == "date_asc":
            emails.sort(key=lambda x: x.get('date_received', ''))
        elif sort_by == "sender_asc":
            emails.sort(key=lambda x: x.get('sender', ''))
        elif sort_by == "subject_asc":
            emails.sort(key=lambda x: x.get('subject', ''))
        
        # 페이징
        return emails[offset:offset + limit]
    
    def save_email(self, email_data: Dict[str, Any]) -> str:
        """이메일을 저장하고 ID를 반환합니다."""
        emails = self._load_json(self.emails_file)
        
        # ID가 없으면 새로 생성
        if 'id' not in email_data:
            email_data['id'] = str(uuid4())
        
        # datetime 객체를 문자열로 변환
        email_data = self._convert_datetime_to_string(email_data)
        
        # 기존 이메일인지 확인 (파일 해시로)
        file_hash = email_data.get('file_hash')
        if file_hash:
            for i, existing_email in enumerate(emails):
                if existing_email.get('file_hash') == file_hash:
                    # 기존 이메일 업데이트
                    emails[i] = email_data
                    self._save_json(self.emails_file, emails)
                    return email_data['id']
        
        # 새 이메일 추가
        emails.append(email_data)
        self._save_json(self.emails_file, emails)
        return email_data['id']
    
    def _convert_datetime_to_string(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """딕셔너리 내의 datetime 객체를 문자열로 변환합니다."""
        converted = data.copy()
        for key, value in converted.items():
            if isinstance(value, datetime):
                converted[key] = value.isoformat()
        return converted
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """ID로 이메일을 조회합니다."""
        emails = self._load_json(self.emails_file)
        for email in emails:
            if email.get('id') == email_id:
                return email
        return None
    
    def get_all_tags(self) -> List[Dict[str, Any]]:
        """모든 활성 태그를 반환합니다."""
        tags = self._load_json(self.tags_file)
        
        # 태그가 배열 형태인지 확인
        if isinstance(tags, list):
            return [tag for tag in tags if isinstance(tag, dict) and tag.get('is_active', True)]
        elif isinstance(tags, dict):
            # TagConfig 딕셔너리 형태를 배열로 변환
            converted_tags = []
            for korean_name, tag_info in tags.items():
                converted_tag = {
                    "id": korean_name,
                    "name": korean_name,
                    "display_name": korean_name,
                    "description": tag_info.get('description', ''),
                    "color": tag_info.get('color', '#007ACC'),
                    "is_system": korean_name in ["중요", "회신필요", "스팸", "광고"],
                    "is_active": True,
                    "ai_prompt": tag_info.get('prompt', ''),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                converted_tags.append(converted_tag)
            return converted_tags
        else:
            return []
    
    def assign_tags_to_email(self, email_id: str, tag_names: List[str]):
        """이메일에 태그를 할당합니다."""
        emails = self._load_json(self.emails_file)
        
        for i, email in enumerate(emails):
            if email.get('id') == email_id:
                email['tags'] = list(set(email.get('tags', []) + tag_names))
                emails[i] = email
                self._save_json(self.emails_file, emails)
                break
    
    def get_generated_replies_for_email(self, original_email_id: str) -> List[Dict[str, Any]]:
        """특정 이메일에 대해 생성된 답장들을 반환합니다."""
        emails = self._load_json(self.emails_file)
        
        replies = []
        for email in emails:
            if (email.get('is_generated_reply', False) and 
                email.get('original_email_id') == original_email_id):
                replies.append(email)
        
        # 날짜순으로 정렬 (최신순)
        replies.sort(key=lambda x: x.get('date_sent', ''), reverse=True)
        return replies
    
    def delete_email(self, email_id: str) -> bool:
        """이메일을 삭제합니다."""
        emails = self._load_json(self.emails_file)
        
        for i, email in enumerate(emails):
            if email.get('id') == email_id:
                emails.pop(i)
                self._save_json(self.emails_file, emails)
                return True
        return False
    
    def delete_emails(self, email_ids: List[str]) -> Dict[str, Any]:
        """여러 이메일을 삭제합니다."""
        emails = self._load_json(self.emails_file)
        original_count = len(emails)
        
        emails = [email for email in emails if email.get('id') not in email_ids]
        deleted_count = original_count - len(emails)
        
        self._save_json(self.emails_file, emails)
        
        return {
            'success_count': deleted_count,
            'failed_count': len(email_ids) - deleted_count
        }
    
    def get_email_count(self) -> int:
        """전체 이메일 수를 반환합니다."""
        emails = self._load_json(self.emails_file)
        return len(emails)
    
    def close(self):
        """연결을 종료합니다 (JSON에서는 실제로 할 일이 없음)."""
        pass 