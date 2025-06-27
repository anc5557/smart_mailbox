# src/smart_mailbox/ai/reply_gen.py
from typing import Dict, Any
from .ollama_client import OllamaClient

class ReplyGenerator:
    """
    AI를 사용하여 이메일 답장을 생성하는 클래스
    """
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    def set_client(self, ollama_client: OllamaClient):
        """Ollama 클라이언트를 업데이트합니다."""
        self.ollama_client = ollama_client

    def generate_reply(self, email_data: Dict[str, Any]) -> str:
        """
        주어진 이메일 데이터에 대한 답장을 생성합니다.

        :param email_data: 원본 이메일 데이터 딕셔너리
        :return: 생성된 답장 텍스트
        """
        try:
            # 이메일 내용 준비
            subject = email_data.get('subject', '')
            sender = email_data.get('sender', '')
            body_text = email_data.get('body_text', '') or ''
            
            # 답장 생성을 위한 이메일 내용 구성
            email_content = f"""제목: {subject}
발신자: {sender}
본문:
{body_text[:1500]}"""  # 본문 길이 제한
            
            prompt = f"""
다음 이메일에 대한 전문적이고 간결한 답장 초안을 작성해주세요. 
답장은 원본 이메일의 핵심 내용을 파악하고, 적절한 조치를 제안하거나 질문에 답변해야 합니다.

**규칙:**
- 한국어로 작성하세요.
- 불필요한 미사여구 없이 핵심만 전달하세요.
- 긍정적이고 협조적인 톤을 유지하세요.
- 마무리 인사는 "감사합니다." 또는 "안부 전합니다."로 통일하세요.

--- 원본 이메일 ---
{email_content}
--------------------

**답장 초안:**
"""
            
            response = self.ollama_client.generate_completion(prompt)
            if response:
                return response.strip()
            return "답장 생성 중 오류가 발생했습니다."
        except Exception as e:
            print(f"Error generating reply: {e}")
            return "답장 생성 중 오류가 발생했습니다."
