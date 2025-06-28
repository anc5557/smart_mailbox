"""
업데이트 확인 모듈
"""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from datetime import datetime

from .version_manager import VersionManager
from ..config.logger import logger


class UpdateChecker:
    """애플리케이션 업데이트를 확인하는 클래스"""
    
    def __init__(self, repo_owner: str = "anc5557", repo_name: str = "smart_mailbox"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.version_manager = VersionManager()
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    
    def check_for_updates(self, timeout: int = 10) -> Dict[str, Any]:
        """
        GitHub에서 최신 릴리스 정보를 확인합니다.
        
        Args:
            timeout: 요청 타임아웃 (초)
            
        Returns:
            Dict: 업데이트 정보
        """
        try:
            logger.info("업데이트 확인 중...")
            
            # GitHub API 요청
            request = urllib.request.Request(
                self.github_api_url,
                headers={'User-Agent': 'Smart-Mailbox-App'}
            )
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return self._parse_release_data(data)
                else:
                    logger.error(f"GitHub API 응답 오류: {response.status}")
                    return self._create_error_response("API 응답 오류")
                    
        except urllib.error.URLError as e:
            logger.error(f"네트워크 오류: {e}")
            return self._create_error_response("네트워크 연결 오류")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return self._create_error_response("응답 데이터 파싱 오류")
        except Exception as e:
            logger.error(f"업데이트 확인 오류: {e}")
            return self._create_error_response(f"알 수 없는 오류: {str(e)}")
    
    def _parse_release_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """GitHub API 응답 데이터를 파싱합니다."""
        try:
            remote_version = data.get('tag_name', '').lstrip('v')
            current_version = self.version_manager.get_current_version()
            
            # 새 버전 여부 확인
            has_update = self.version_manager.is_newer_version(remote_version)
            
            # 릴리스 노트에서 한국어 부분 추출
            release_notes = data.get('body', '')
            if release_notes:
                # 간단한 마크다운 정리
                release_notes = release_notes.replace('## ', '• ').replace('# ', '• ')
                release_notes = release_notes.replace('**', '').replace('*', '')
            
            # 발행일 파싱
            published_at = data.get('published_at', '')
            if published_at:
                try:
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    published_date = pub_date.strftime('%Y년 %m월 %d일')
                except:
                    published_date = published_at
            else:
                published_date = "알 수 없음"
            
            # 다운로드 URL 찾기
            download_url = data.get('html_url', '')
            assets = data.get('assets', [])
            for asset in assets:
                if asset.get('name', '').endswith(('.exe', '.dmg', '.zip')):
                    download_url = asset.get('browser_download_url', download_url)
                    break
            
            result = {
                'success': True,
                'has_update': has_update,
                'current_version': current_version,
                'latest_version': remote_version,
                'release_name': data.get('name', f'v{remote_version}'),
                'release_notes': release_notes,
                'published_date': published_date,
                'download_url': download_url,
                'is_prerelease': data.get('prerelease', False)
            }
            
            logger.info(f"업데이트 확인 완료: 현재 {current_version}, 최신 {remote_version}, 업데이트 필요: {has_update}")
            return result
            
        except Exception as e:
            logger.error(f"릴리스 데이터 파싱 오류: {e}")
            return self._create_error_response("데이터 파싱 오류")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """오류 응답을 생성합니다."""
        return {
            'success': False,
            'error': error_message,
            'has_update': False,
            'current_version': self.version_manager.get_current_version(),
            'latest_version': None
        }
    
    def get_current_version_info(self) -> Dict[str, Any]:
        """현재 버전 정보를 반환합니다."""
        return self.version_manager.get_version_info() 