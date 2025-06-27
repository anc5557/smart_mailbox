# src/smart_mailbox/ai/tagger.py
import json
import logging
from typing import Dict, List, Optional

from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class Tagger:
    """
    AI를 사용하여 이메일에 태그를 지정하는 단순화된 클래스
    """
    def __init__(self, ollama_client: OllamaClient, storage_manager=None):
        self.ollama_client = ollama_client
        self.storage_manager = storage_manager
        
        # 단순화된 분류 프롬프트 템플릿
        self.simple_classification_template = """메일 분류:

제목: {subject}
발신자: {sender}
본문: {body}

태그들:
{tag_descriptions}

적용할 태그를 JSON 배열로 반환하세요:"""

    def set_storage_manager(self, storage_manager):
        """스토리지 매니저를 설정합니다."""
        self.storage_manager = storage_manager

    def get_tag_prompts(self) -> Dict[str, str]:
        """활성화된 태그들의 프롬프트를 가져옵니다."""
        try:
            if self.storage_manager:
                if hasattr(self.storage_manager, 'get_tag_prompts_for_ai'):
                    tag_prompts = self.storage_manager.get_tag_prompts_for_ai()
                    print(f"📋 AI 태깅용 태그 프롬프트 로드됨: {list(tag_prompts.keys())}")
                    return tag_prompts
                else:
                    # get_all_tags 메서드를 사용하여 태그 프롬프트 구성
                    db_tags = self.storage_manager.get_all_tags()
                    
                    tag_prompts = {}
                    for tag in db_tags:
                        if isinstance(tag, dict):
                            tag_name = tag.get('name', '')
                            ai_prompt = tag.get('ai_prompt', '')
                            is_active = tag.get('is_active', True)
                            
                            if is_active and ai_prompt and tag_name:
                                tag_prompts[tag_name] = ai_prompt
                                print(f"📌 태그 '{tag_name}' 프롬프트 로드됨")
                    
                    print(f"📋 총 {len(tag_prompts)}개의 AI 태깅용 태그 로드됨")
                    return tag_prompts
            else:
                print("⚠️ 스토리지 매니저가 설정되지 않았습니다.")
                return {}
                
        except Exception as e:
            print(f"❌ 태그 프롬프트 로드 실패: {e}")
            return {}

    def analyze_email(self, email_data: Dict) -> Optional[List[str]]:
        """단순화된 이메일 분석을 통해 태그를 반환합니다."""
        try:
            tag_prompts = self.get_tag_prompts()
            
            if not tag_prompts:
                print("⚠️ 사용 가능한 태그 프롬프트가 없습니다.")
                return []
            
            print(f"🤖 AI 태깅 시작: {email_data.get('subject', '')[:50]}...")
            
            # 태그 설명 문자열 생성
            tag_descriptions = ""
            for tag_name, tag_description in tag_prompts.items():
                tag_descriptions += f"- {tag_name}: {tag_description}\n"
            
            # body_text 안전하게 처리
            body_text = email_data.get('body_text', '') or ''
            body_content = body_text[:1000] if body_text else ''
            
            # 단순한 프롬프트로 한 번에 모든 태그 분류
            prompt = self.simple_classification_template.format(
                subject=email_data.get('subject', ''),
                sender=email_data.get('sender', ''),
                body=body_content,
                tag_descriptions=tag_descriptions
            )
            
            response = self.ollama_client.generate_completion(prompt, temperature=0.1)
            
            if response:
                tags = self._parse_tag_array(response, list(tag_prompts.keys()))
                print(f"✅ AI 태깅 완료: {tags}")
                return tags
            else:
                print("⚠️ AI 응답 없음")
                return []
                
        except Exception as e:
            print(f"❌ 이메일 분석 중 오류 발생: {e}")
            logger.exception("이메일 분석 중 예외 발생")
            return None

    def _parse_tag_array(self, response: str, available_tags: List[str]) -> List[str]:
        """AI 응답에서 태그 배열을 파싱합니다."""
        try:
            # JSON 응답에서 배열 추출
            response = response.strip()
            
            # JSON 블록 찾기
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            
            # JSON 파싱 시도
            try:
                parsed = json.loads(response)
                if isinstance(parsed, list):
                    # 유효한 태그만 필터링
                    valid_tags = [tag for tag in parsed if tag in available_tags]
                    return valid_tags
                elif isinstance(parsed, dict):
                    # 딕셔너리 형태인 경우 tags 키에서 추출 또는 값들에서 추출
                    print(f"🔍 딕셔너리 응답 처리: {parsed}")
                    if 'tags' in parsed:
                        tags = parsed['tags']
                        if isinstance(tags, list):
                            valid_tags = [tag for tag in tags if tag in available_tags]
                            return valid_tags
                    # tags 키가 없으면 값들 중에서 태그 찾기
                    found_tags = []
                    for value in parsed.values():
                        if isinstance(value, str) and value in available_tags:
                            found_tags.append(value)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, str) and item in available_tags:
                                    found_tags.append(item)
                    return found_tags
                else:
                    print(f"⚠️ 예상한 형태가 아님: {type(parsed)}")
                    return []
            except json.JSONDecodeError:
                # JSON 파싱 실패시 텍스트에서 태그 추출
                return self._extract_tags_from_text(response, available_tags)
                
        except Exception as e:
            print(f"⚠️ 태그 파싱 실패: {e}")
            return []

    def _extract_tags_from_text(self, text: str, available_tags: List[str]) -> List[str]:
        """텍스트에서 태그를 추출합니다."""
        found_tags = []
        for tag in available_tags:
            if tag in text:
                found_tags.append(tag)
        return found_tags

    # 호환성을 위한 레거시 메서드들
    def analyze_email_detailed(self, email_data: Dict) -> Dict[str, any]:
        """단순화된 분석 결과를 기존 형식으로 반환합니다."""
        tags = self.analyze_email(email_data)
        return {
            'tags': tags or [],
            'confidence': 0.8,
            'method': 'simplified_ai_tagging'
        } 