"""
Ollama LLM 클라이언트 - ollama 라이브러리 사용
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

import ollama
from ollama import Client, ResponseError

from ..config.ai import AIConfig

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Ollama 설정"""
    base_url: str = "http://localhost:11434"
    timeout: int = 60
    max_retries: int = 3
    disable_thinking: bool = True  # thinking 비활성화 (ollama의 think=False 적용)


class OllamaClient:
    """
    Ollama LLM 클라이언트 - ollama 라이브러리 사용
    
    thinking 모드 제어:
    - config.disable_thinking=True (기본값): ollama의 think=False로 thinking 비활성화
    - config.disable_thinking=False: ollama의 think=True로 thinking 활성화
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None, ai_config: Optional[AIConfig] = None):
        self.config = config or OllamaConfig()
        self.ai_config = ai_config or AIConfig(Path.home() / ".smart_mailbox")
        
        # ollama 클라이언트 초기화
        self.client = Client(
            host=self.config.base_url,
            timeout=self.config.timeout
        )

    def is_available(self) -> bool:
        """Ollama 서버 연결 상태 확인"""
        try:
            # 간단한 모델 목록 요청으로 연결 확인
            self.client.list()
            return True
        except Exception as e:
            logger.warning(f"Ollama 서버 연결 실패: {e}")
            return False

    def check_connection(self) -> tuple[bool, List[str]]:
        """
        Ollama 서버 연결 상태와 사용 가능한 모델 목록을 확인합니다.
        
        Returns:
            (bool, List[str]): (연결 성공 여부, 모델 이름 목록)
        """
        if not self.is_available():
            return False, []
        
        models = self.get_available_models()
        return True, models
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 조회"""
        try:
            result = self.client.list()
            # ollama 라이브러리는 pydantic 모델을 반환하므로 .model 속성을 사용
            # None 값을 필터링하여 타입 안전성 확보
            return [model.model for model in result.models if model.model is not None]
        except Exception as e:
            logger.error(f"Ollama 모델 목록 조회 실패: {e}")
            return []
    
    def _get_best_available_model(self, preferred_model: Optional[str] = None) -> Optional[str]:
        """설정된 모델이 없거나 사용할 수 없을 때 사용 가능한 모델을 선택합니다."""
        model = preferred_model or self.ai_config.get_model()
        
        # 모델 이름이 비어있으면 기본값 사용
        if not model or model.strip() == "":
            model = self.ai_config.default_settings["model"]
            logger.warning(f"모델 이름이 비어있어 기본값 '{model}'을 사용합니다.")
        
        # 사용 가능한 모델 목록 확인
        available_models = self.get_available_models()
        
        if not available_models:
            logger.error("사용 가능한 모델이 없습니다. Ollama 서버와 모델 설치를 확인하세요.")
            return None
        
        # 설정된 모델이 사용 가능한지 확인
        if model in available_models:
            return model
        
        # 설정된 모델이 없으면 사용 가능한 첫 번째 모델 사용
        logger.warning(f"설정된 모델 '{model}'을 찾을 수 없습니다. 사용 가능한 모델: {available_models}")
        selected_model = available_models[0]
        logger.info(f"사용 가능한 첫 번째 모델 '{selected_model}'을 사용합니다.")
        return selected_model

    def generate_completion(self, prompt: str, model: Optional[str] = None, 
                          temperature: float = 0.1, max_tokens: Optional[int] = None) -> Optional[str]:
        """텍스트 생성 완료"""
        
        # 최적의 모델 선택
        selected_model = self._get_best_available_model(model)
        if not selected_model:
            return None
        
        try:
            # ollama.generate 사용
            options = {
                "temperature": temperature,
            }
            
            if max_tokens:
                options["num_predict"] = max_tokens
            
            # thinking 비활성화 설정 적용
            think_enabled = not self.config.disable_thinking
            
            response = self.client.generate(
                model=selected_model,
                prompt=prompt,
                options=options,
                think=think_enabled
            )
            
            logger.info(f"생성 응답: {response}")
            
            if response and hasattr(response, 'response'):
                try:
                    raw_text = response.response
                    if raw_text is not None:
                        raw_text = raw_text.strip()
                        # thinking 비활성화가 되어있어도 안전을 위해 후처리 유지
                        cleaned_text = self._clean_thinking_tags(raw_text)
                        return cleaned_text if cleaned_text else None
                except AttributeError as e:
                    logger.error(f"응답 속성 접근 오류: {e}")
                    return None
            
            return None
            
        except ResponseError as e:
            logger.error(f"Ollama 응답 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return None
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                       temperature: float = 0.1, max_tokens: Optional[int] = None) -> Optional[str]:
        """채팅 완료 (대화형)"""
        
        # 최적의 모델 선택
        selected_model = self._get_best_available_model(model)
        if not selected_model:
            return None
        
        try:
            # ollama.chat 사용
            options = {
                "temperature": temperature,
            }
            
            if max_tokens:
                options["num_predict"] = max_tokens
            
            # thinking 비활성화 설정 적용
            think_enabled = not self.config.disable_thinking
            
            response = self.client.chat(
                model=selected_model,
                messages=messages,
                options=options,
                think=think_enabled
            )
            
            if response and hasattr(response, 'message'):
                raw_content = response.message.content.strip() if response.message.content else ""
                # thinking 비활성화가 되어있어도 안전을 위해 후처리 유지
                cleaned_content = self._clean_thinking_tags(raw_content)
                return cleaned_content if cleaned_content else None
            
            return None
            
        except ResponseError as e:
            logger.error(f"Ollama 응답 오류: {e}")
            return None
        except Exception as e:
            logger.error(f"채팅 LLM 호출 실패: {e}")
            return None

    def _clean_thinking_tags(self, text: str) -> str:
        """응답에서 thinking 태그와 그 내용을 제거합니다."""
        if not text:
            return ""
        
        import re
        
        # <think>...</think> 또는 <thinking>...</thinking> 패턴 제거
        patterns = [
            r'<think>.*?</think>',
            r'<thinking>.*?</thinking>',
            r'<think>.*',  # 닫는 태그가 없는 경우
            r'<thinking>.*',  # 닫는 태그가 없는 경우
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        # 연속된 공백이나 줄바꿈 정리
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def close(self):
        """클라이언트 종료"""
        # ollama 클라이언트는 별도 종료 메서드가 없음
        pass


class EmailTagger:
    """이메일 자동 태깅 AI"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
        
    def classify_email(self, email_data: Dict[str, Any], tags_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        이메일 분류 및 태깅
        
        Args:
            email_data: 이메일 데이터
            tags_config: 태그 설정 목록
            
        Returns:
            분류 결과 (태그 이름 목록 및 신뢰도)
        """
        
        # 이메일 내용 준비
        email_content = self._prepare_email_content(email_data)
        
        # 각 태그에 대해 분류 수행
        classification_results = []
        
        for tag_config in tags_config:
            tag_name = tag_config.get("name")
            tag_prompt = tag_config.get("ai_prompt")
            
            if not tag_prompt or not tag_name:
                continue
            
            # 분류 프롬프트 생성
            prompt = self._create_classification_prompt(email_content, tag_prompt, tag_name)
            
            # LLM 호출
            response = self._classify_with_llm(prompt)
            
            if response:
                # 응답 파싱
                result = self._parse_classification_response(response, tag_name)
                if result["should_tag"]:
                    classification_results.append(result)
        
        # 결과 정리
        assigned_tags = [result["tag_name"] for result in classification_results]
        confidence_scores = {result["tag_name"]: result["confidence"] for result in classification_results}
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "tags": assigned_tags,
            "confidence_scores": confidence_scores,
            "overall_confidence": avg_confidence,
            "classification_details": classification_results
        }
    
    def _prepare_email_content(self, email_data: Dict[str, Any]) -> str:
        """분석용 이메일 내용 준비"""
        parts = []
        
        # 제목
        if email_data.get("subject"):
            parts.append(f"제목: {email_data['subject']}")
        
        # 발신자
        if email_data.get("sender"):
            sender_info = email_data["sender"]
            if email_data.get("sender_name"):
                sender_info = f"{email_data['sender_name']} <{sender_info}>"
            parts.append(f"발신자: {sender_info}")
        
        # 수신자
        if email_data.get("recipient"):
            recipient_info = email_data["recipient"]
            if email_data.get("recipient_name"):
                recipient_info = f"{email_data['recipient_name']} <{recipient_info}>"
            parts.append(f"수신자: {recipient_info}")
        
        # 본문 (텍스트 우선, 없으면 HTML에서 텍스트 추출)
        body = email_data.get("body_text")
        if not body and email_data.get("body_html"):
            # 간단한 HTML 태그 제거 (정확한 파싱은 별도 라이브러리 사용)
            import re
            body = re.sub(r'<[^>]+>', '', email_data["body_html"])
            body = body.strip()
        
        if body:
            # 본문이 너무 길면 일부만 사용
            if len(body) > 2000:
                body = body[:2000] + "..."
            parts.append(f"본문:\n{body}")
        
        return "\n\n".join(parts)
    
    def _create_classification_prompt(self, email_content: str, tag_prompt: str, tag_name: str) -> str:
        """분류용 프롬프트 생성"""
        return f"""다음 이메일을 분석하여 '{tag_name}' 태그가 적절한지 판단해주세요.

판단 기준:
{tag_prompt}

이메일 내용:
{email_content}

응답 형식은 다음과 같이 해주세요:
판단: [적절함/부적절함]
신뢰도: [0.0-1.0]
이유: [간단한 설명]"""
    
    def _classify_with_llm(self, prompt: str) -> Optional[str]:
        """LLM을 통한 분류 수행"""
        return self.ollama.generate_completion(prompt, temperature=0.1)
    
    def _parse_classification_response(self, response: str, tag_name: str) -> Dict[str, Any]:
        """분류 응답 파싱"""
        # 간단한 파싱 로직 (실제로는 더 정교하게 구현)
        should_tag = "적절함" in response or "yes" in response.lower()
        
        # 신뢰도 추출 시도
        confidence = 0.5
        import re
        confidence_match = re.search(r'신뢰도[:：]\s*([0-9.]+)', response)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
            except ValueError:
                pass
        
        return {
            "tag_name": tag_name,
            "should_tag": should_tag,
            "confidence": confidence,
            "reasoning": response
        }


class ReplyGenerator:
    """이메일 답장 생성기"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def generate_reply(self, email_data: Dict[str, Any], reply_tone: str = "professional") -> Optional[str]:
        """
        이메일 답장 생성
        
        Args:
            email_data: 원본 이메일 데이터
            reply_tone: 답장 톤 (professional, friendly, formal 등)
            
        Returns:
            생성된 답장 텍스트
        """
        
        # 이메일 내용 준비
        email_content = self._prepare_email_for_reply(email_data)
        
        # 답장 생성 프롬프트 작성
        prompt = self._create_reply_prompt(email_content, reply_tone)
        
        # LLM으로 답장 생성
        generated_reply = self._generate_with_llm(prompt)
        
        if generated_reply:
            # 답장 형식 정리
            return self._format_reply(generated_reply, email_data)
        
        return None
    
    def _prepare_email_for_reply(self, email_data: Dict[str, Any]) -> str:
        """답장 생성용 이메일 내용 준비"""
        parts = []
        
        if email_data.get("subject"):
            parts.append(f"제목: {email_data['subject']}")
        
        if email_data.get("sender"):
            parts.append(f"발신자: {email_data['sender']}")
        
        body = email_data.get("body_text", "")
        if body:
            if len(body) > 1500:
                body = body[:1500] + "..."
            parts.append(f"본문:\n{body}")
        
        return "\n\n".join(parts)
    
    def _create_reply_prompt(self, email_content: str, reply_tone: str) -> str:
        """답장 생성 프롬프트 작성"""
        tone_descriptions = {
            "professional": "전문적이고 비즈니스적인 톤",
            "friendly": "친근하고 따뜻한 톤",
            "formal": "격식있고 공식적인 톤"
        }
        
        tone_desc = tone_descriptions.get(reply_tone, "전문적인 톤")
        
        return f"""다음 이메일에 대한 답장을 {tone_desc}으로 작성해주세요.

원본 이메일:
{email_content}

답장 작성 가이드라인:
- 한국어로 작성
- {tone_desc} 유지
- 구체적이고 도움이 되는 내용
- 적절한 인사말과 마무리 포함

답장:"""
    
    def _generate_with_llm(self, prompt: str) -> Optional[str]:
        """LLM으로 텍스트 생성"""
        return self.ollama.generate_completion(prompt, temperature=0.3)
    
    def _format_reply(self, generated_reply: str, original_email: Dict[str, Any]) -> str:
        """답장 형식 정리"""
        # 간단한 형식 정리
        reply = generated_reply.strip()
        
        # 필요하면 제목 라인 추가
        if not reply.startswith("제목:") and original_email.get("subject"):
            subject = original_email["subject"]
            if not subject.startswith("Re:"):
                reply = f"제목: Re: {subject}\n\n{reply}"
        
        return reply 