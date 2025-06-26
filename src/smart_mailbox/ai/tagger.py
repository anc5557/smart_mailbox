# src/smart_mailbox/ai/tagger.py
import json
import logging
from typing import Dict, Any, List

from .ollama_client import OllamaClient
from ..config.tags import TagConfig

logger = logging.getLogger(__name__)

class Tagger:
    """
    AI를 사용하여 이메일에 태그를 지정하는 클래스
    """
    def __init__(self, ollama_client: OllamaClient, tag_config: TagConfig):
        self.ollama_client = ollama_client
        self.tag_config = tag_config

    def set_client(self, ollama_client: OllamaClient):
        """Ollama 클라이언트를 업데이트합니다."""
        self.ollama_client = ollama_client

    def tag_email(self, email_content: str) -> Dict[str, Any]:
        """
        주어진 이메일 내용에 대해 모든 태그를 평가하고, 가장 적합한 태그를 반환합니다.

        :param email_content: 분석할 이메일의 본문 내용
        :return: 태그 분석 결과 (가장 가능성 높은 태그, 각 태그의 신뢰도 점수 등)
        """
        all_tags = self.tag_config.get_all_tags()
        
        tag_definitions = [
            f"- **{name}**: {details['prompt']}"
            for name, details in all_tags.items()
        ]
        
        prompt = f"""
        당신은 이메일을 분석하고 가장 적절한 태그를 지정하는 AI 어시스턴트입니다.
        다음 이메일 내용을 읽고, 아래에 정의된 태그 중에서 가장 적합한 태그들을 **하나 이상** 선택해주세요.

        **분석할 이메일:**
        ---
        {email_content[:2000]}
        ---

        **사용 가능한 태그 정의:**
        {chr(10).join(tag_definitions)}

        **출력 형식:**
        반드시 다음 JSON 형식에 맞춰 응답해주세요. 다른 설명은 절대 추가하지 마세요.
        {{
          "reasoning": "이메일 내용에 기반한 간단한 분석 이유 (예: '프로젝트 마감일 언급으로 중요 태그 선택')",
          "tags": [
            {{
              "name": "태그 이름",
              "match": true,
              "confidence": "0.0에서 1.0 사이의 신뢰도 점수"
            }},
            ...
          ]
        }}

        **규칙:**
        - 모든 태그에 대해 `match` 여부와 `confidence` 점수를 평가해야 합니다.
        - `match`는 해당 태그가 이메일 내용과 일치하는지 여부를 나타내는 boolean 값입니다.
        - `confidence`는 AI가 얼마나 확신하는지를 나타내는 0.0에서 1.0 사이의 숫자입니다.
        - 하나 이상의 태그에 대해 `match`를 `true`로 설정해야 합니다.
        - JSON 형식만 출력하고, 다른 텍스트는 절대 포함하지 마세요.
        """

        try:
            raw_response = self.ollama_client.generate_completion(prompt)
            
            if not raw_response:
                logger.error("AI로부터 응답을 받지 못했습니다.")
                return {
                    "error": "AI로부터 응답을 받지 못했습니다. Ollama 서버와 모델 설정을 확인하세요.", 
                    "raw_response": None,
                    "matched_tags": [],
                    "confidence_scores": {}
                }
            
            # LLM 응답에서 JSON 부분만 추출
            json_response_str = self._extract_json(raw_response)
            if not json_response_str:
                logger.error("AI 응답에서 JSON 객체를 찾을 수 없습니다.")
                return {
                    "error": "AI 응답 형식이 잘못되었습니다. JSON 형식의 응답을 받지 못했습니다.", 
                    "raw_response": raw_response,
                    "matched_tags": [],
                    "confidence_scores": {}
                }

            parsed_json = json.loads(json_response_str)
            return self._validate_and_structure_response(parsed_json)

        except json.JSONDecodeError as e:
            logger.error(f"AI 응답 JSON 파싱 실패: {e}\n응답 내용: {raw_response}")
            return {
                "error": f"AI 응답을 해석할 수 없습니다: {str(e)}", 
                "raw_response": raw_response,
                "matched_tags": [],
                "confidence_scores": {}
            }
        except Exception as e:
            logger.error(f"이메일 태깅 중 오류 발생: {e}")
            return {
                "error": f"이메일 태깅 중 오류가 발생했습니다: {str(e)}",
                "matched_tags": [],
                "confidence_scores": {}
            }

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

    def _validate_and_structure_response(self, parsed_json: Dict) -> Dict:
        """파싱된 JSON을 검증하고 구조화합니다."""
        if "tags" not in parsed_json or not isinstance(parsed_json["tags"], list):
            raise ValueError("응답에 'tags' 필드가 없거나 리스트가 아닙니다.")

        # 필터링된 태그와 신뢰도 점수
        matched_tags = [
            tag["name"] for tag in parsed_json["tags"] 
            if tag.get("match") is True and tag.get("name") in self.tag_config.get_tag_names()
        ]
        
        confidence_scores = {
            tag.get("name"): float(tag.get("confidence", 0.0))
            for tag in parsed_json["tags"]
            if tag.get("name") in self.tag_config.get_tag_names()
        }

        return {
            "matched_tags": matched_tags,
            "confidence_scores": confidence_scores,
            "reasoning": parsed_json.get("reasoning", ""),
            "raw_response": parsed_json
        } 