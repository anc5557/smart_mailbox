# src/smart_mailbox/config/ai.py
import json
from pathlib import Path
from typing import Dict, Any
from ..config.logger import logger

class AIConfig:
    """
    AI 관련 설정을 관리하는 클래스
    """
    def __init__(self, config_path: Path):
        # ollama.json 파일을 다른 설정 파일들과 같은 위치에 저장 (~/SmartMailbox/)
        from pathlib import Path
        data_dir = Path.home() / "SmartMailbox"
        self.config_file = data_dir / "ollama.json"
        self.default_settings = {
            "model": "llama3.2",  # 기본값은 그대로 유지
            "temperature": 0.7,
            "max_tokens": 1024,
            "disable_thinking": True,  # thinking 비활성화 기본값
            "server_url": "http://localhost:11434",
            "timeout": 60
        }
        self.settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """
        설정 파일에서 AI 설정을 로드하고, 없으면 기본값으로 생성합니다.
        """
        if not self.config_file.exists():
            self._save_settings(self.default_settings)
            return self.default_settings
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                stored_settings = json.load(f)
                # 기본 설정과 저장된 설정을 병합하여 새로운 키 추가에 대응
                updated_settings = self.default_settings.copy()
                updated_settings.update(stored_settings)
                return updated_settings
        except Exception as e:
            logger.error(f"AI 설정 파일을 읽는 중 오류 발생: {e}. 기본 설정으로 복원합니다.")
            self._save_settings(self.default_settings)
            return self.default_settings

    def _save_settings(self, settings: Dict[str, Any]):
        """
        AI 설정을 파일에 저장합니다.
        """
        # SmartMailbox 디렉터리 생성 (다른 설정 파일들과 같은 위치)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        특정 설정 값을 가져옵니다.
        """
        return self.settings.get(key, default)

    def update_settings(self, new_settings: Dict[str, Any]):
        """
        설정을 업데이트하고 파일에 저장합니다.
        """
        self.settings.update(new_settings)
        self._save_settings(self.settings)

    def get_model(self) -> str:
        """
        현재 설정된 AI 모델 이름을 반환합니다.
        """
        return self.get_setting("model", self.default_settings["model"])

    def is_thinking_disabled(self) -> bool:
        """
        thinking 비활성화 설정 여부를 반환합니다.
        """
        return self.get_setting("disable_thinking", self.default_settings["disable_thinking"])

    def set_thinking_disabled(self, disabled: bool):
        """
        thinking 비활성화 설정을 변경합니다.
        """
        self.update_settings({"disable_thinking": disabled})
