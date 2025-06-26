# src/smart_mailbox/config/tags.py
import json
from pathlib import Path
from typing import Dict, List, Any

class TagConfig:
    """
    기본 및 커스텀 태그 설정을 관리하는 클래스
    """
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_file = self.config_path / "tags.json"
        self.default_tags = {
            "중요": {"color": "#FF0000", "prompt": "이 이메일이 긴급하거나 매우 중요한 내용을 포함하는지 판단합니다."},
            "회신필요": {"color": "#0000FF", "prompt": "이 이메일이 명시적 또는 암묵적으로 답장을 요구하는지 판단합니다."},
            "스팸": {"color": "#808080", "prompt": "이 이메일이 원치 않는 스팸 또는 정크 메일인지 판단합니다."},
            "광고": {"color": "#FFA500", "prompt": "이 이메일이 제품 또는 서비스의 마케팅이나 광고인지 판단합니다."}
        }
        self.tags = self._load_tags()

    def _load_tags(self) -> Dict[str, Any]:
        """
        설정 파일에서 태그를 로드하고, 없으면 기본값으로 생성합니다.
        """
        if not self.config_file.exists():
            self._save_tags(self.default_tags)
            return self.default_tags
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                # 기본 태그와 저장된 커스텀 태그를 병합
                stored_tags = json.load(f)
                # 기본 태그의 프롬프트나 색상이 변경되었을 수 있으므로 업데이트
                updated_tags = self.default_tags.copy()
                updated_tags.update(stored_tags)
                return updated_tags
        except (json.JSONDecodeError, IOError) as e:
            print(f"태그 설정 파일을 읽는 중 오류 발생: {e}. 기본 설정으로 복원합니다.")
            self._save_tags(self.default_tags)
            return self.default_tags

    def _save_tags(self, tags: Dict[str, Any]):
        """
        태그 설정을 파일에 저장합니다.
        """
        self.config_path.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(tags, f, ensure_ascii=False, indent=4)

    def get_all_tags(self) -> Dict[str, Any]:
        """
        모든 태그(기본 + 커스텀)를 반환합니다.
        """
        return self.tags

    def get_tag_names(self) -> List[str]:
        """
        모든 태그의 이름 목록을 반환합니다.
        """
        return list(self.tags.keys())

    def add_custom_tag(self, name: str, color: str, prompt: str) -> bool:
        """
        새로운 커스텀 태그를 추가합니다.
        """
        if name in self.tags:
            print(f"오류: '{name}' 태그가 이미 존재합니다.")
            return False
        
        self.tags[name] = {"color": color, "prompt": prompt, "is_custom": True}
        self._save_tags(self.tags)
        return True

    def update_custom_tag(self, name: str, new_color: str, new_prompt: str) -> bool:
        """
        커스텀 태그의 속성을 업데이트합니다.
        """
        if name not in self.tags or not self.tags[name].get("is_custom", False):
            print(f"오류: '{name}'는 수정할 수 없는 기본 태그이거나 존재하지 않는 태그입니다.")
            return False
            
        if new_color:
            self.tags[name]["color"] = new_color
        if new_prompt:
            self.tags[name]["prompt"] = new_prompt
            
        self._save_tags(self.tags)
        return True

    def delete_custom_tag(self, name: str) -> bool:
        """
        커스텀 태그를 삭제합니다.
        """
        if name not in self.tags or not self.tags[name].get("is_custom", False):
            print(f"오류: '{name}'는 삭제할 수 없는 기본 태그이거나 존재하지 않는 태그입니다.")
            return False
            
        del self.tags[name]
        self._save_tags(self.tags)
        return True
