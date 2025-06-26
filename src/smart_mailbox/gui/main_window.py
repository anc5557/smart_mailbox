"""
AI Smart Mailbox 메인 윈도우
"""
import sys
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QLineEdit, QLabel,
    QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QTimer
from PyQt6.QtGui import QAction

from .sidebar import Sidebar
from .email_view import EmailView
from .settings import SettingsDialog
from ..storage import DatabaseManager
from ..storage.file_manager import FileManager
from ..config import TagConfig, AIConfig
from ..ai import OllamaClient, OllamaConfig, Tagger, ReplyGenerator


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""
    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_filter = {}
        self.settings = QSettings()
        self.init_core_components()
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.connect_signals()
        self.load_initial_data()
        
        # 초기 테마 적용 (중요!)
        current_theme = self.settings.value("general/theme", "auto", type=str)
        print(f"🎨 초기 테마 적용: {current_theme}")  # 디버깅용
        self.theme_changed.emit(current_theme)
        
        # Ollama 연결 상태 확인 및 표시
        self.check_initial_ollama_status()

    def init_core_components(self):
        """핵심 백엔드 컴포넌트 초기화"""
        try:
            self.file_manager = FileManager()
            self.db_manager = DatabaseManager(str(self.file_manager.get_db_path()))
            self.tag_config = TagConfig(self.file_manager.get_tags_config_path())
            self.ai_config = AIConfig(self.file_manager.get_config_path())
            
            self.load_settings() # 설정 먼저 로드
            
            # Ollama 설정 적용
            ollama_settings = self.settings.value("ollama", {}, type=dict)
            ollama_config = OllamaConfig(
                base_url=ollama_settings.get("server_url", "http://localhost:11434"),
                timeout=ollama_settings.get("timeout", 60)
            )
            self.ollama_client = OllamaClient(ollama_config, self.ai_config) 
            self.tagger = Tagger(self.ollama_client, self.tag_config)
            self.reply_generator = ReplyGenerator(self.ollama_client)
        except Exception as e:
            QMessageBox.critical(self, "초기화 오류", f"애플리케이션 핵심 컴포넌트 초기화 실패: {e}")
            sys.exit(1)

    def setup_ui(self):
        """메인 UI 구성"""
        self.setWindowTitle("🤖 AI Smart Mailbox")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯
        central_widget = QWidget()
        central_widget.setContentsMargins(0, 0, 0, 0)  # 중앙 위젯의 마진도 제거
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 검색바를 맨 상단에 헤더로 배치
        self.setup_search_bar(main_layout)
        
        # 메인 컨텐츠 (사이드바 + 이메일 뷰)
        self.setup_main_content(main_layout)
        
        # 상태바
        self.statusBar().showMessage("Ready")

    def setup_search_bar(self, layout: QVBoxLayout):
        """검색바 설정 - 헤더 스타일"""
        search_widget = QWidget()
        search_widget.setObjectName("searchWidget")
        search_widget.setFixedHeight(50)  # 고정 높이로 제한
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(15, 8, 15, 8)  # 패딩 줄임
        search_layout.setSpacing(10)
        
        search_label = QLabel("🔍")
        search_label.setObjectName("searchLabel")
        search_layout.addWidget(search_label)
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("searchBar")
        self.search_bar.setPlaceholderText("이메일 제목, 내용, 발신자 검색...")
        self.search_bar.setFixedHeight(32)  # 고정 높이로 더 줄임
        
        # 검색바 스타일링
        self.search_bar.setStyleSheet("""
            QLineEdit#searchBar {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                background-color: #f8f9fa;
            }
            QLineEdit#searchBar:focus {
                border: 2px solid #0078d4;
                background-color: #ffffff;
                outline: none;
            }
        """)
        
        search_layout.addWidget(self.search_bar)
        
        # 검색 위젯 전체 스타일링 - 헤더 느낌으로
        search_widget.setStyleSheet("""
            QWidget#searchWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e1e5e9;
            }
            QLabel#searchLabel {
                font-weight: 600;
                font-size: 16px;
                color: #495057;
                min-width: 30px;
                max-width: 30px;
            }
        """)
        
        layout.addWidget(search_widget)

    def setup_main_content(self, layout: QVBoxLayout):
        """메인 컨텐츠 영역 설정"""
        # 메인 영역 (사이드바 + 이메일 뷰)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 사이드바
        self.sidebar = Sidebar()
        splitter.addWidget(self.sidebar)
        
        # 이메일 뷰
        self.email_view = EmailView()
        splitter.addWidget(self.email_view)
        
        # 사이즈 비율: 사이드바 20%, 이메일 뷰 80%
        splitter.setSizes([250, 950])
        
        layout.addWidget(splitter)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("파일(&F)")
        open_action = QAction("이메일 파일 열기(&O)", self)
        open_action.triggered.connect(self.open_email_files)
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        exit_action = QAction("종료(&X)", self)
        exit_action.triggered.connect(lambda: None if self.close() else None)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("설정(&S)")
        preferences_action = QAction("환경설정(&P)", self)
        preferences_action.triggered.connect(self.show_settings)
        settings_menu.addAction(preferences_action)

    def setup_toolbar(self):
        """툴바 설정"""
        # 현재는 툴바 없음, 필요하면 나중에 추가
        pass

    def connect_signals(self):
        self.sidebar.tag_selected.connect(self.filter_by_tag)
        self.sidebar.home_selected.connect(self.email_view.show_home_view)
        self.email_view.status_changed.connect(self.statusBar().showMessage)
        
        # 이메일 뷰의 파일 처리 시그널 연결
        self.email_view.files_processing.connect(self.process_email_files)
        
        # 검색창 입력 시 0.5초 후 자동 검색
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.trigger_search)
        self.search_bar.textChanged.connect(lambda: self.search_timer.start(500))

    def load_initial_data(self):
        self.load_tags()
        self.load_emails()

    def load_tags(self):
        try:
            all_tags = self.tag_config.get_all_tags()
            # TODO: DB에서 태그별 카운트 가져오는 로직 개선
            tags_data = [{'name': name, 'display_name': name, 'color': details['color'], 'count': 0} for name, details in all_tags.items()]
            self.sidebar.update_tags(tags_data)
        except Exception as e:
            self.statusBar().showMessage(f"태그 로드 실패: {e}")

    def load_emails(self):
        try:
            # TODO: 실제 데이터베이스에서 이메일 로드
            emails_data = []  # 임시로 빈 목록
            self.email_view.update_email_list(emails_data)
        except Exception as e:
            self.statusBar().showMessage(f"이메일 로드 실패: {e}")

    def filter_by_tag(self, tag_name: str):
        """태그로 필터링"""
        self.current_filter = {'tag': tag_name}
        self.email_view.filter_by_tag(tag_name)
        # TODO: 실제 필터링 로직 구현
        self.statusBar().showMessage(f"'{tag_name}' 태그로 필터링")

    def trigger_search(self):
        """검색 실행"""
        query = self.search_bar.text().strip()
        if query:
            self.current_filter = {'search': query}
            # TODO: 검색 로직 구현
            self.statusBar().showMessage(f"'{query}' 검색 중...")
        else:
            self.current_filter = {}
            self.statusBar().showMessage("검색 해제")

    def open_email_files(self):
        """이메일 파일 열기"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "이메일 파일 선택", "", "이메일 파일 (*.eml);;모든 파일 (*.*)"
        )
        if file_paths:
            self.process_email_files(file_paths)

    def check_ollama_connection(self) -> bool:
        """Ollama 연결 상태 확인"""
        try:
            is_connected, models = self.ollama_client.check_connection()
            if not is_connected:
                QMessageBox.warning(
                    self,
                    "Ollama 연결 실패",
                    "Ollama 서버에 연결할 수 없습니다.\n\n"
                    "확인사항:\n"
                    "• Ollama가 실행 중인지 확인하세요\n"
                    "• 서버 URL이 올바른지 확인하세요\n"
                    "• 네트워크 연결을 확인하세요\n\n"
                    "설정에서 Ollama 서버 URL을 확인해보세요."
                )
                return False
            
            # 설정된 모델이 사용 가능한지 확인
            current_model = self.ai_config.get_model()
            if current_model not in models:
                QMessageBox.warning(
                    self,
                    "모델 사용 불가",
                    f"설정된 모델 '{current_model}'을 사용할 수 없습니다.\n\n"
                    f"사용 가능한 모델: {', '.join(models) if models else '없음'}\n\n"
                    "설정에서 사용 가능한 모델로 변경하거나,\n"
                    "Ollama에서 해당 모델을 다운로드하세요."
                )
                return False
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ollama 연결 오류",
                f"Ollama 서버 연결 확인 중 오류가 발생했습니다:\n\n{str(e)}\n\n"
                "설정을 확인하고 다시 시도해보세요."
            )
            return False

    def process_email_files(self, file_paths: List[str]):
        """이메일 파일 처리 - Ollama 연결 확인 포함"""
        # Ollama 연결 상태 확인
        if not self.check_ollama_connection():
            self.statusBar().showMessage("Ollama 연결 실패 - 파일 처리가 중단되었습니다.", 5000)
            return
        
        valid_files = [path for path in file_paths if path.endswith('.eml')]
        if not valid_files:
            QMessageBox.warning(self, "경고", "유효한 .eml 파일이 없습니다.")
            return
        
        try:
            from ..email.parser import EmailParser
            
            # 처리 진행률 표시
            total_files = len(valid_files)
            self.email_view.show_processing_progress(0, total_files)
            
            parser = EmailParser()
            processed_emails = []
            errors = []
            
            for i, file_path in enumerate(valid_files):
                try:
                    self.statusBar().showMessage(f"파일 파싱 중... ({i+1}/{total_files}): {file_path}")
                    
                    # 이메일 파싱
                    email_data = parser.parse_eml_file(file_path)
                    
                    # AI 태깅 수행
                    self.statusBar().showMessage(f"AI 태깅 중... ({i+1}/{total_files})")
                    
                    # 이메일 내용 준비
                    email_content = f"제목: {email_data.get('subject', '')}\n"
                    email_content += f"발신자: {email_data.get('sender', '')}\n"
                    if email_data.get('body_text'):
                        email_content += f"내용: {email_data['body_text'][:1000]}"
                    
                    tagging_result = self.tagger.tag_email(email_content)
                    
                    # 태깅 결과 확인 및 처리
                    if 'error' in tagging_result:
                        error_msg = f"{file_path}: AI 태깅 실패 - {tagging_result['error']}"
                        errors.append(error_msg)
                        print(f"태깅 오류: {error_msg}")
                        
                        # 태깅 실패한 경우에도 기본 정보는 저장
                        email_data['ai_processed'] = False
                        email_data['assigned_tags'] = []
                        email_data['tag_confidence'] = 0.0
                        email_data['tagging_error'] = tagging_result['error']
                    else:
                        # 태깅 결과 추가
                        email_data['ai_processed'] = True
                        email_data['assigned_tags'] = tagging_result.get('matched_tags', [])
                        email_data['tag_confidence'] = sum(tagging_result.get('confidence_scores', {}).values()) / max(len(tagging_result.get('confidence_scores', {})), 1)
                    
                    # 데이터베이스에 저장
                    # TODO: 데이터베이스 저장 로직 구현
                    processed_emails.append(email_data)
                    
                    # 진행률 업데이트
                    self.email_view.show_processing_progress(i + 1, total_files)
                    
                except Exception as e:
                    error_msg = f"{file_path}: {str(e)}"
                    errors.append(error_msg)
                    print(f"파일 처리 오류: {error_msg}")
            
            # 처리 완료
            self.email_view.hide_processing_progress()
            
            # 결과 메시지
            success_count = len(processed_emails)
            error_count = len(errors)
            
            if success_count > 0:
                message = f"✅ {success_count}개 이메일이 성공적으로 처리되었습니다."
                if error_count > 0:
                    message += f"\n⚠️ {error_count}개 파일에서 오류가 발생했습니다."
                
                # 성공한 이메일 목록 표시
                if processed_emails:
                    self.email_view.update_email_list(processed_emails)
                    self.load_tags()  # 태그 목록 새로고침
                
                QMessageBox.information(self, "처리 완료", message)
                self.statusBar().showMessage(f"이메일 처리 완료: {success_count}개 성공", 5000)
            else:
                error_details = "\n".join(errors[:5])  # 최대 5개 오류만 표시
                if len(errors) > 5:
                    error_details += f"\n... 및 {len(errors) - 5}개 추가 오류"
                
                QMessageBox.critical(
                    self,
                    "처리 실패",
                    f"모든 파일 처리에 실패했습니다.\n\n오류 내용:\n{error_details}"
                )
                self.statusBar().showMessage("파일 처리 실패", 5000)
            
        except ImportError as e:
            QMessageBox.critical(
                self,
                "모듈 오류",
                f"필요한 모듈을 가져올 수 없습니다:\n{str(e)}\n\n개발자에게 문의하세요."
            )
        except Exception as e:
            self.email_view.hide_processing_progress()
            QMessageBox.critical(
                self,
                "파일 처리 오류",
                f"이메일 파일 처리 중 예상치 못한 오류가 발생했습니다:\n\n{str(e)}"
            )
            self.statusBar().showMessage("파일 처리 실패", 5000)

    def show_settings(self):
        """설정 대화상자 표시"""
        dialog = SettingsDialog(self.tag_config, self.ai_config, self)
        
        # 설정 변경 시그널 연결
        dialog.settings_changed.connect(self.save_settings)
        
        # 현재 설정 로드
        current_settings = {
            'general': {
                'theme': self.settings.value("general/theme", "auto", type=str),
                'auto_start': self.settings.value("general/auto_start", False, type=bool),
                'minimize_to_tray': self.settings.value("general/minimize_to_tray", False, type=bool),
                'auto_save': self.settings.value("general/auto_save", True, type=bool),
                'auto_backup': self.settings.value("general/auto_backup", False, type=bool),
                'backup_days': self.settings.value("general/backup_days", 7, type=int)
            },
            'ollama': {
                'server_url': self.settings.value("ollama/server_url", "http://localhost:11434", type=str),
                'model': self.ai_config.get_model(),
                'timeout': self.settings.value("ollama/timeout", 60, type=int),
                'temperature': self.settings.value("ollama/temperature", 0.7, type=float),
                'max_tokens': self.settings.value("ollama/max_tokens", 2000, type=int)
            },
            'tags': self.tag_config.get_all_tags()
        }
        
        dialog.load_settings(current_settings)
        dialog.exec()

    def save_settings(self, new_settings):
        """설정 저장"""
        try:
            # AI 관련 설정은 AIConfig에 저장
            if 'ollama' in new_settings:
                ollama_settings = new_settings.pop('ollama')
                self.ai_config.update_settings({
                    'model': ollama_settings.get('model'),
                    'temperature': ollama_settings.get('temperature'),
                    'max_tokens': ollama_settings.get('max_tokens')
                })
                # 나머지 ollama 설정은 QSettings에 저장
                self.settings.setValue("ollama/server_url", ollama_settings.get('server_url'))
                self.settings.setValue("ollama/timeout", ollama_settings.get('timeout'))

            # 기존 설정과 비교하여 변경사항만 처리
            old_theme = self.settings.value("general/theme", "auto", type=str)
            new_theme = new_settings.get('general', {}).get('theme', 'auto')
            
            print(f"🎨 테마 변경: {old_theme} → {new_theme}")  # 디버깅용
            
            # 나머지 모든 설정 저장
            for section, section_settings in new_settings.items():
                for key, value in section_settings.items():
                    self.settings.setValue(f"{section}/{key}", value)
                    print(f"💾 설정 저장: {section}/{key} = {value}")  # 디버깅용
            
            # 설정 즉시 반영 (중요!)
            self.settings.sync()
            
            # 테마가 변경되었으면 테마 적용 (qdarktheme가 자동으로 모든 위젯 업데이트)
            if old_theme != new_theme:
                print(f"✅ 테마 변경 시그널 발송: {new_theme}")  # 디버깅용
                self.theme_changed.emit(new_theme)
            
            # Ollama 설정이 변경되었으면 재로드
            self.reload_components_on_settings_change()
                
            self.statusBar().showMessage("설정이 저장되었습니다", 3000)
        except Exception as e:
            print(f"❌ 설정 저장 오류: {e}")  # 디버깅용
            QMessageBox.critical(self, "설정 저장 실패", f"설정 저장 중 오류가 발생했습니다: {e}")
            self.statusBar().showMessage("설정 저장 실패", 3000)

    def load_settings(self):
        """QSettings에서 설정을 로드합니다."""
        # 기본값 설정
        if not self.settings.contains("general/theme"):
            self.settings.setValue("general/theme", "auto")
        if not self.settings.contains("ollama/server_url"):
            self.settings.setValue("ollama/server_url", "http://localhost:11434")
        if not self.settings.contains("ollama/timeout"):
            self.settings.setValue("ollama/timeout", 60)

    def reload_components_on_settings_change(self):
        """설정 변경에 따라 영향을 받는 컴포넌트를 다시 로드합니다."""
        # Ollama 클라이언트 재설정
        try:
            self.ollama_client.close() # 기존 클라이언트 종료
            ollama_settings = self.settings.value("ollama", {}, type=dict)
            ollama_config = OllamaConfig(
                base_url=ollama_settings.get("server_url", "http://localhost:11434"),
                timeout=ollama_settings.get("timeout", 60)
            )
            self.ollama_client = OllamaClient(ollama_config, self.ai_config)
            self.tagger.set_client(self.ollama_client)
            # ReplyGenerator 인스턴스 재생성 (set_client 대신)
            self.reply_generator = ReplyGenerator(self.ollama_client)
            self.statusBar().showMessage("Ollama 설정이 업데이트되었습니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", f"Ollama 클라이언트 재설정 중 오류 발생: {e}")

        # 태그 다시 로드
        self.load_tags()

    def check_initial_ollama_status(self):
        """애플리케이션 시작 시 Ollama 연결 상태 확인"""
        try:
            is_connected, models = self.ollama_client.check_connection()
            if is_connected:
                model_info = f"({len(models)}개 모델)" if models else "(모델 없음)"
                self.statusBar().showMessage(f"✅ Ollama 연결됨 {model_info}", 5000)
            else:
                self.statusBar().showMessage("⚠️ Ollama 연결 실패 - 설정에서 확인하세요", 10000)
        except Exception as e:
            self.statusBar().showMessage(f"❌ Ollama 연결 오류: {str(e)[:50]}...", 10000)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 