# src/smart_mailbox/config/tags.py
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..config.logger import logger

class TagConfig:
    """
    기본 및 커스텀 태그 설정을 관리하는 클래스
    """
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_file = self.config_path / "tags.json"
        
        # 개선된 기본 태그 설정 (초기화용)
        self.initial_default_tags = {
            "중요": {
                "color": "#FF0000", 
                "prompt": "긴급, 중요, ASAP, 마감, 결재, 승인 등 중요한 키워드가 있는 메일"
            },
            "회신필요": {
                "color": "#0000FF", 
                "prompt": "질문, 확인 요청, 회의 일정, 피드백 요청 등 답변이 필요한 메일"
            },
            "스팸": {
                "color": "#808080", 
                "prompt": "광고, 의심스러운 발신자, 피싱, 사기 등으로 의심되는 메일"
            },
            "광고": {
                "color": "#FFA500", 
                "prompt": "마케팅, 홍보, 할인, 이벤트, 뉴스레터 등 상업적 목적의 메일"
            }
        }
        self.tags = self._load_tags()

    def _load_tags(self) -> Dict[str, Any]:
        """
        설정 파일에서 태그를 로드하고, 없으면 기본값으로 생성합니다.
        """
        if not self.config_file.exists():
            self._save_tags(self.initial_default_tags)
            return self.initial_default_tags
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                stored_data = json.load(f)
                
                # 배열 형태인지 딕셔너리 형태인지 확인
                if isinstance(stored_data, list):
                    # JSONStorageManager가 생성한 배열 형태의 태그 데이터
                    # 기본 태그로 시작하여 기존 설정 파일을 새 형태로 변환
                    logger.info("기존 JSON 스토리지 태그 형태를 TagConfig 형태로 변환합니다.")
                    self._save_tags(self.initial_default_tags)
                    return self.initial_default_tags
                elif isinstance(stored_data, dict):
                    # 기존 TagConfig 형태의 딕셔너리 데이터
                    # 기본 태그가 없는 경우에만 추가 (처음 시작할 때만)
                    if not stored_data:
                        return self.initial_default_tags
                    
                    # 기본 태그 중 누락된 것이 있다면 추가
                    updated_tags = stored_data.copy()
                    added_any = False
                    for tag_name, tag_data in self.initial_default_tags.items():
                        if tag_name not in updated_tags:
                            updated_tags[tag_name] = tag_data
                            added_any = True
                            logger.info(f"누락된 기본 태그 '{tag_name}' 추가됨")
                    
                    if added_any:
                        self._save_tags(updated_tags)
                    
                    return updated_tags
                else:
                    # 알 수 없는 형태
                    logger.warning("알 수 없는 태그 파일 형태입니다. 기본 설정으로 복원합니다.")
                    self._save_tags(self.initial_default_tags)
                    return self.initial_default_tags
                    
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"태그 설정 파일을 읽는 중 오류 발생: {e}. 기본 설정으로 복원합니다.")
            self._save_tags(self.initial_default_tags)
            return self.initial_default_tags

    def _save_tags(self, tags: Dict[str, Any]):
        """
        태그 설정을 파일에 저장합니다.
        """
        self.config_path.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(tags, f, ensure_ascii=False, indent=4)

    def get_all_tags(self) -> Dict[str, Any]:
        """
        모든 태그를 반환합니다.
        """
        return self.tags

    def get_tag_names(self) -> List[str]:
        """
        모든 태그의 이름 목록을 반환합니다.
        """
        return list(self.tags.keys())

    def add_tag(self, name: str, color: str = '#007ACC', prompt: str = '') -> bool:
        """
        새로운 태그를 추가합니다.
        """
        if name in self.tags:
            logger.error(f"오류: '{name}' 태그가 이미 존재합니다.")
            return False
        
        self.tags[name] = {"color": color, "prompt": prompt}
        self._save_tags(self.tags)
        logger.info(f"새 태그 '{name}' 추가됨")
        return True

    def update_tag(self, name: str, color: Optional[str] = None, prompt: Optional[str] = None) -> bool:
        """
        태그의 속성을 업데이트합니다. 이제 모든 태그(기본 태그 포함) 수정 가능합니다.
        """
        if name not in self.tags:
            logger.error(f"오류: '{name}' 태그가 존재하지 않습니다.")
            return False
            
        if color is not None:
            self.tags[name]["color"] = color
        if prompt is not None:
            self.tags[name]["prompt"] = prompt
            
        self._save_tags(self.tags)
        logger.info(f"태그 '{name}' 업데이트됨")
        return True

    def delete_tag(self, name: str) -> bool:
        """
        태그를 삭제합니다. 이제 모든 태그(기본 태그 포함) 삭제 가능합니다.
        """
        if name not in self.tags:
            logger.error(f"오류: '{name}' 태그가 존재하지 않습니다.")
            return False
            
        del self.tags[name]
        self._save_tags(self.tags)
        logger.info(f"태그 '{name}' 삭제됨")
        return True

    def reset_to_defaults(self) -> bool:
        """
        모든 태그를 초기 기본 태그로 재설정합니다.
        """
        self.tags = self.initial_default_tags.copy()
        self._save_tags(self.tags)
        logger.info("태그가 기본 설정으로 재설정됨")
        return True

    # 호환성을 위한 레거시 메서드들 (deprecated)
    def add_custom_tag(self, name: str, color: str, prompt: str) -> bool:
        """호환성을 위한 메서드. add_tag를 사용하세요."""
        return self.add_tag(name, color, prompt)

    def update_custom_tag(self, name: str, new_color: str, new_prompt: str) -> bool:
        """호환성을 위한 메서드. update_tag를 사용하세요."""
        return self.update_tag(name, new_color, new_prompt)

    def delete_custom_tag(self, name: str) -> bool:
        """호환성을 위한 메서드. delete_tag를 사용하세요."""
        return self.delete_tag(name)
