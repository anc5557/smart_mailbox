# src/smart_mailbox/ai/tagger.py
import json
import logging
from typing import Dict, Any, List, Optional

from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class Tagger:
    """
    AI를 사용하여 이메일에 태그를 지정하는 클래스
    """
    def __init__(self, ollama_client: OllamaClient, storage_manager=None):
        self.ollama_client = ollama_client
        self.storage_manager = storage_manager
        self.prompt_template = """
다음 이메일의 내용을 분석하여 적절한 태그를 선택해주세요:

{prompt_info}

이메일:
제목: {subject}
보낸사람: {sender}
본문: {body}

위의 이메일을 분석하여 해당하는 태그가 있다면 그 태그의 이름만 콤마로 구분하여 응답해주세요.
해당하는 태그가 없다면 "없음"이라고 응답해주세요.

응답 예시:
- 해당하는 태그가 있는 경우: 중요, 회신필요
- 해당하는 태그가 없는 경우: 없음

응답:"""

    def set_storage_manager(self, storage_manager):
        """스토리지 매니저를 설정합니다."""
        self.storage_manager = storage_manager

    def get_tag_prompts(self) -> Dict[str, str]:
        """활성화된 태그들의 프롬프트를 가져옵니다."""
        try:
            # 스토리지 매니저에서 태그 프롬프트 가져오기
            if self.storage_manager:
                # JSONStorageManager의 get_tag_prompts_for_ai 메서드 사용
                if hasattr(self.storage_manager, 'get_tag_prompts_for_ai'):
                    tag_prompts = self.storage_manager.get_tag_prompts_for_ai()
                    print(f"📋 AI 태깅용 태그 프롬프트 로드됨: {list(tag_prompts.keys())}")
                    return tag_prompts
                else:
                    # get_all_tags 메서드를 사용하여 태그 프롬프트 구성
                    db_tags = self.storage_manager.get_all_tags()
                    
                    # 태그 프롬프트 딕셔너리 구성
                    tag_prompts = {}
                    for tag in db_tags:
                        # tag가 딕셔너리인지 확인
                        if isinstance(tag, dict):
                            tag_name = tag.get('name', '')
                            ai_prompt = tag.get('ai_prompt', '')
                            is_active = tag.get('is_active', True)
                            
                            if is_active and ai_prompt and tag_name:
                                tag_prompts[tag_name] = ai_prompt
                                print(f"📌 태그 '{tag_name}' 프롬프트 로드됨")
                            else:
                                print(f"⚠️ 태그 '{tag_name}': is_active={is_active}, ai_prompt='{ai_prompt}'")
                        else:
                            print(f"⚠️ 예상치 못한 태그 형태: {type(tag)} - {tag}")
                    
                    print(f"📋 총 {len(tag_prompts)}개의 AI 태깅용 태그 로드됨")
                    return tag_prompts
            else:
                print("⚠️ 스토리지 매니저가 설정되지 않았습니다.")
                return {}
                
        except Exception as e:
            print(f"❌ 태그 프롬프트 로드 실패: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def analyze_email(self, email_data: Dict) -> Optional[List[str]]:
        """이메일을 분석하여 태그를 반환합니다."""
        try:
            # 태그 프롬프트 가져오기
            tag_prompts = self.get_tag_prompts()
            
            if not tag_prompts:
                print("⚠️ 사용 가능한 태그 프롬프트가 없습니다.")
                return []
            
            # 프롬프트 정보 구성
            prompt_info = "태그 목록:\n"
            for tag_name, description in tag_prompts.items():
                prompt_info += f"- {tag_name}: {description}\n"
            
            # 최종 프롬프트 구성
            prompt = self.prompt_template.format(
                prompt_info=prompt_info,
                subject=email_data.get('subject', ''),
                sender=email_data.get('sender', ''),
                body=email_data.get('body_text', '')[:1000]  # 본문 길이 제한
            )
            
            print(f"🤖 AI 태깅 요청: {email_data.get('subject', '')[:50]}...")
            
            # AI에게 분석 요청
            response = self.ollama_client.generate_completion(prompt)
            
            if response:
                # 응답에서 태그 추출
                tags = self._parse_tags_from_response(response, list(tag_prompts.keys()))
                print(f"✅ AI 태깅 결과: {tags}")
                return tags
            else:
                print("❌ AI 응답을 받지 못했습니다.")
                return None
                
        except Exception as e:
            print(f"❌ 이메일 분석 중 오류 발생: {e}")
            return None
    
    def _parse_tags_from_response(self, response: str, available_tags: List[str]) -> List[str]:
        """AI 응답에서 태그를 파싱합니다."""
        try:
            # 응답에서 태그 추출
            tags = []
            
            print(f"🔍 AI 응답 분석 중: {response[:200]}...")
            
            # "없음" 또는 "해당 없음" 등의 응답 체크
            if any(no_tag in response.lower() for no_tag in ['없음', '해당 없음', 'none', '해당하는 태그가 없', '태그 없음']):
                print("ℹ️ AI가 해당하는 태그가 없다고 응답했습니다.")
                return []
            
            # 전체 응답에서 직접 태그명 검색
            response_lower = response.lower()
            for available_tag in available_tags:
                tag_found = False
                
                # 태그명이 응답에 포함되어 있는지 확인
                if available_tag in response:
                    # 컨텍스트 확인 - 부정적인 컨텍스트가 아닌지 체크
                    tag_position = response.find(available_tag)
                    
                    # 태그 앞뒤 문맥을 확인 (최대 50자)
                    start = max(0, tag_position - 50)
                    end = min(len(response), tag_position + len(available_tag) + 50)
                    context = response[start:end].lower()
                    
                    # 부정적 표현이 있는지 확인
                    negative_words = ['아니요', 'no', 'false', '아님', '없음', '해당 없음', '적용 안됨', '해당되지 않음']
                    has_negative = any(neg in context for neg in negative_words)
                    
                    # 긍정적 표현이 있는지 확인
                    positive_words = ['예', 'yes', 'true', '해당', '적용', '맞음']
                    has_positive = any(pos in context for pos in positive_words)
                    
                    if has_negative:
                        print(f"❌ 태그 '{available_tag}' 제외됨 (부정적 컨텍스트): {context}")
                    elif has_positive or not has_negative:
                        # 명시적인 부정이 없으면 포함
                        tag_found = True
                        print(f"✅ 태그 '{available_tag}' 발견됨 (컨텍스트): {context}")
                
                if tag_found and available_tag not in tags:
                    tags.append(available_tag)
            
            # 태그가 없으면 더 세밀한 분석 시도
            if not tags:
                print("🔄 세밀한 분석으로 재시도...")
                
                # 줄별로 분석
                lines = response.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 콤마로 구분된 태그들 찾기
                    if ',' in line:
                        parts = line.split(',')
                        for part in parts:
                            part = part.strip().strip('.-')
                            for available_tag in available_tags:
                                if part == available_tag and available_tag not in tags:
                                    tags.append(available_tag)
                                    print(f"✅ 태그 매칭됨 (콤마 구분): '{available_tag}'")
                    else:
                        # 단일 태그 확인
                        line_clean = line.strip('.-: ')
                        for available_tag in available_tags:
                            if line_clean == available_tag and available_tag not in tags:
                                tags.append(available_tag)
                                print(f"✅ 태그 매칭됨 (단일): '{available_tag}'")
            
            print(f"📊 최종 매칭된 태그: {tags}")
            return tags
            
        except Exception as e:
            print(f"❌ 태그 파싱 중 오류: {e}")
            return []

    def _extract_json(self, text: str) -> str:
        """문자열에서 JSON 객체 또는 배열을 추출합니다."""
        # ```json ... ``` 코드 블록 처리
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]

        # 첫 '{' 또는 '[' 부터 마지막 '}' 또는 ']' 까지 추출
        start_brace = text.find('{')
        start_bracket = text.find('[')
        
        if start_brace == -1 and start_bracket == -1:
            return ""

        if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
            start = start_brace
            end = text.rfind('}')
        else:
            start = start_bracket
            end = text.rfind(']')

        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        
        return ""

    def _validate_and_structure_response(self, parsed_json: Dict, korean_mapping: Dict = {}) -> Dict:
        """파싱된 JSON을 검증하고 구조화합니다."""
        if "tags" not in parsed_json or not isinstance(parsed_json["tags"], list):
            raise ValueError("응답에 'tags' 필드가 없거나 리스트가 아닙니다.")

        # 검증된 태그명 목록 (한국어)
        if korean_mapping:
            valid_korean_names = set(korean_mapping.values())
        else:
            valid_korean_names = {"중요", "회신필요", "스팸", "광고"}

        # 필터링된 태그와 신뢰도 점수
        matched_tags = [
            tag["name"] for tag in parsed_json["tags"] 
            if tag.get("match") is True and tag.get("name") in valid_korean_names
        ]
        
        confidence_scores = {
            tag.get("name"): float(tag.get("confidence", 0.0))
            for tag in parsed_json["tags"]
            if tag.get("name") in valid_korean_names
        }

        return {
            "matched_tags": matched_tags,
            "confidence_scores": confidence_scores,
            "reasoning": parsed_json.get("reasoning", ""),
            "raw_response": parsed_json
        } 