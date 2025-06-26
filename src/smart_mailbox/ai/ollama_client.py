"""
Ollama LLM 클라이언트
"""

import json
import logging
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

from ..config.ai import AIConfig

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Ollama 설정"""
    base_url: str = "http://localhost:11434"
    timeout: int = 60
    max_retries: int = 3
    disable_thinking: bool = True  # thinking 비활성화 기본값


class OllamaClient:
    """Ollama LLM 클라이언트"""
    
    def __init__(self, config: Optional[OllamaConfig] = None, ai_config: Optional[AIConfig] = None):
        self.config = config or OllamaConfig()
        self.ai_config = ai_config or AIConfig(Path.home() / ".smart_mailbox")
        self.client = httpx.Client(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        )
    
    def _get_thinking_stop_tokens(self) -> List[str]:
        """thinking 비활성화를 위한 중단 토큰 목록 반환"""
        # AI 설정에서 thinking 비활성화 설정을 우선적으로 확인
        disable_thinking = self.ai_config.is_thinking_disabled() if self.ai_config else self.config.disable_thinking
        
        if disable_thinking:
            return [
                "<thinking>",
                "<think>", 
                "thinking:",
                "Think:",
                "생각:",
                "[생각]",
                "분석:",
                "[분석]"
            ]
        return []

    def is_available(self) -> bool:
        """Ollama 서버 연결 상태 확인"""
        try:
            # HEAD 요청으로 빠르게 확인
            response = self.client.head("/")
            response.raise_for_status()
            return True
        except httpx.RequestError as e:
            logger.warning(f"Ollama 서버 연결 실패 (HEAD): {e}")
            # GET 요청으로 다시 시도
            try:
                response = self.client.get("/")
                response.raise_for_status()
                return True
            except httpx.RequestError as e2:
                logger.warning(f"Ollama 서버 연결 실패 (GET): {e2}")
                return False
        except httpx.HTTPStatusError as e:
            logger.warning(f"Ollama 서버 응답 오류: {e.response.status_code}")
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
            response = self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except httpx.RequestError as e:
            logger.error(f"Ollama 모델 목록 조회 실패: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama 모델 목록 조회 응답 오류: {e.response.status_code}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ollama 모델 목록 응답 파싱 실패: {e}")
            return []
    
    def generate_completion(self, prompt: str, model: Optional[str] = None, 
                          temperature: float = 0.1, max_tokens: Optional[int] = None) -> Optional[str]:
        """텍스트 생성 완료"""
        model = model or self.ai_config.get_model()
        
        # 모델 이름이 비어있으면 기본값 사용
        if not model or model.strip() == "":
            model = self.ai_config.default_settings["model"]
            logger.warning(f"모델 이름이 비어있어 기본값 '{model}'을 사용합니다.")
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            # thinking 비활성화를 위한 stop 토큰 추가
            thinking_stop_tokens = self._get_thinking_stop_tokens()
            if thinking_stop_tokens:
                payload["options"]["stop"] = thinking_stop_tokens
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            response = self.client.post("/api/generate", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"생성 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"LLM 호출 실패: {e}")
            return None
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                       temperature: float = 0.1, max_tokens: Optional[int] = None) -> Optional[str]:
        """채팅 완료 (대화형)"""
        model = model or self.ai_config.get_model()
        
        # 모델 이름이 비어있으면 기본값 사용
        if not model or model.strip() == "":
            model = self.ai_config.default_settings["model"]
            logger.warning(f"모델 이름이 비어있어 기본값 '{model}'을 사용합니다.")
        
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            # thinking 비활성화를 위한 stop 토큰 추가
            thinking_stop_tokens = self._get_thinking_stop_tokens()
            if thinking_stop_tokens:
                payload["options"]["stop"] = thinking_stop_tokens
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            response = self.client.post("/api/chat", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", {})
                return message.get("content", "").strip()
            else:
                logger.error(f"채팅 완료 실패: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"채팅 LLM 호출 실패: {e}")
            return None
    
    def close(self):
        """클라이언트 종료"""
        if self.client:
            self.client.close()


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

응답 형식:
- 판단 결과: YES 또는 NO
- 신뢰도: 0.0~1.0 사이의 숫자
- 이유: 간단한 설명

예시:
판단 결과: YES
신뢰도: 0.85
이유: 이메일에 질문이 포함되어 있고 답변을 요청하고 있음

이제 분석해주세요:"""
    
    def _classify_with_llm(self, prompt: str) -> Optional[str]:
        """LLM을 사용한 분류"""
        try:
            # 채팅 형식으로 호출 (더 나은 응답을 위해)
            messages = [
                {
                    "role": "system",
                    "content": "당신은 이메일 분류 전문가입니다. 주어진 기준에 따라 이메일을 정확하게 분류해주세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            return self.ollama.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=200
            )
            
        except Exception as e:
            logger.error(f"LLM 분류 호출 실패: {e}")
            return None
    
    def _parse_classification_response(self, response: str, tag_name: str) -> Dict[str, Any]:
        """LLM 응답 파싱"""
        result = {
            "tag_name": tag_name,
            "should_tag": False,
            "confidence": 0.0,
            "reason": ""
        }
        
        try:
            lines = response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("판단 결과:"):
                    decision = line.split(":", 1)[1].strip().upper()
                    result["should_tag"] = decision == "YES"
                    
                elif line.startswith("신뢰도:"):
                    confidence_str = line.split(":", 1)[1].strip()
                    try:
                        confidence = float(confidence_str)
                        result["confidence"] = max(0.0, min(1.0, confidence))
                    except ValueError:
                        result["confidence"] = 0.5
                        
                elif line.startswith("이유:"):
                    result["reason"] = line.split(":", 1)[1].strip()
            
            # 기본값 처리
            if result["should_tag"] and result["confidence"] == 0.0:
                result["confidence"] = 0.7  # 기본 신뢰도
                
        except Exception as e:
            logger.error(f"응답 파싱 실패: {e}")
            
        return result


class ReplyGenerator:
    """AI 답장 생성기"""
    
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def generate_reply(self, email_data: Dict[str, Any], reply_tone: str = "professional") -> Optional[str]:
        """
        이메일 답장 생성
        
        Args:
            email_data: 원본 이메일 데이터
            reply_tone: 답장 톤 (professional, friendly, casual)
            
        Returns:
            생성된 답장 내용
        """
        
        # 이메일 내용 준비
        email_content = self._prepare_email_for_reply(email_data)
        
        # 답장 생성 프롬프트 생성
        prompt = self._create_reply_prompt(email_content, reply_tone)
        
        # LLM 호출
        response = self._generate_with_llm(prompt)
        
        if response:
            return self._format_reply(response, email_data)
        
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
            # 본문 길이 제한
            if len(body) > 1500:
                body = body[:1500] + "..."
            parts.append(f"내용:\n{body}")
        
        return "\n\n".join(parts)
    
    def _create_reply_prompt(self, email_content: str, reply_tone: str) -> str:
        """답장 생성 프롬프트 생성"""
        tone_instructions = {
            "professional": "전문적이고 정중한 비즈니스 톤으로",
            "friendly": "친근하고 따뜻한 톤으로",
            "casual": "편안하고 자연스러운 톤으로"
        }
        
        tone_instruction = tone_instructions.get(reply_tone, tone_instructions["professional"])
        
        return f"""다음 이메일에 대한 적절한 답장을 {tone_instruction} 작성해주세요.

원본 이메일:
{email_content}

답장 작성 가이드라인:
1. 원본 이메일의 내용을 충분히 이해하고 답변
2. 질문이 있다면 구체적으로 답변
3. 추가 정보가 필요하다면 요청
4. 적절한 인사말과 마무리 포함
5. 한국어로 작성
6. 200-400자 내외의 적절한 길이

답장 내용만 작성해주세요 (제목이나 서명 등은 제외):"""
    
    def _generate_with_llm(self, prompt: str) -> Optional[str]:
        """LLM을 사용한 답장 생성"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": "당신은 전문적인 이메일 작성 도우미입니다. 상황에 맞는 적절하고 정중한 답장을 작성해주세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            return self.ollama.chat_completion(
                messages=messages,
                temperature=0.3,  # 창의성과 일관성의 균형
                max_tokens=500
            )
            
        except Exception as e:
            logger.error(f"답장 생성 LLM 호출 실패: {e}")
            return None
    
    def _format_reply(self, generated_reply: str, original_email: Dict[str, Any]) -> str:
        """답장 형식 정리"""
        reply = generated_reply.strip()
        
        # 불필요한 접두사 제거
        prefixes_to_remove = ["답장:", "답변:", "회신:", "Reply:", "Response:"]
        for prefix in prefixes_to_remove:
            if reply.startswith(prefix):
                reply = reply[len(prefix):].strip()
        
        return reply 