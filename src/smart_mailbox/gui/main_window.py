"""
AI Smart Mailbox 메인 윈도우
"""
import sys
from typing import Dict, Any, List
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QLineEdit, QLabel,
    QFileDialog, QMessageBox, QApplication, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings, QTimer, QThread
from PyQt6.QtGui import QAction

from .sidebar import Sidebar
from .email_view import EmailView
from .settings import SettingsDialog
from ..storage import JSONStorageManager
from ..storage.file_manager import FileManager
from ..config import TagConfig, AIConfig
from ..ai import OllamaClient, OllamaConfig, Tagger, ReplyGenerator


class EmailProcessingWorker(QThread):
    """이메일 처리를 백그라운드에서 수행하는 워커 스레드"""
    
    # 시그널 정의
    progress_updated = pyqtSignal(int, int, str)  # current, total, status_message
    status_updated = pyqtSignal(str)  # status message
    file_processed = pyqtSignal(dict)  # processed email data
    processing_completed = pyqtSignal(list, list)  # processed_emails, errors
    processing_error = pyqtSignal(str)  # error message
    
    def __init__(self, file_paths, components):
        super().__init__()
        self.file_paths = file_paths
        self.file_manager = components['file_manager']
        self.storage_manager = components['storage_manager']
        self.tagger = components['tagger']
        self.is_cancelled = False
    
    def run(self):
        """백그라운드에서 이메일 처리 실행"""
        try:
            from ..email.parser import EmailParser
            
            parser = EmailParser()
            processed_emails = []
            errors = []
            total_files = len(self.file_paths)
            
            # 시작 신호
            self.progress_updated.emit(0, total_files, "📂 파일 처리를 시작합니다...")
            
            for i, file_path in enumerate(self.file_paths):
                if self.is_cancelled:
                    break
                    
                try:
                    import os
                    filename = os.path.basename(file_path)
                    
                    # 파일 파싱 단계
                    self.progress_updated.emit(i, total_files, f"📧 파싱 중: {filename}")
                    self.status_updated.emit(f"파일 파싱 중... ({i+1}/{total_files}): {file_path}")
                    
                    # 이메일 파싱
                    email_data = parser.parse_eml_file(file_path)
                    
                    # 이메일 파일을 애플리케이션 데이터 디렉토리로 복사
                    try:
                        with open(file_path, 'rb') as f:
                            file_content = f.read()
                        
                        saved_path = self.file_manager.save_email_file(file_path, file_content)
                        email_data['file_path'] = str(saved_path)
                    except Exception as copy_error:
                        print(f"파일 복사 실패: {file_path} - {copy_error}")
                    
                    # AI 태깅 단계
                    self.progress_updated.emit(i, total_files, f"🤖 AI 분석 중: {filename}")
                    self.status_updated.emit(f"AI 태깅 중... ({i+1}/{total_files})")
                    
                    if self.is_cancelled:
                        break
                    
                    tagging_result = self.tagger.analyze_email(email_data)
                    
                    # 태깅 결과 처리
                    if tagging_result is not None:
                        email_data['ai_processed'] = True
                        email_data['assigned_tags'] = tagging_result if tagging_result else []
                        email_data['tag_confidence'] = 1.0 if tagging_result else 0.5
                        
                        if tagging_result:
                            print(f"✅ AI 태깅 완료: {email_data['assigned_tags']}")
                        else:
                            print(f"✅ AI 분석 완료 - 해당 태그 없음: {file_path}")
                    else:
                        email_data['ai_processed'] = False
                        email_data['assigned_tags'] = []
                        email_data['tag_confidence'] = 0.0
                        print(f"🚨 AI 태깅 실패: {file_path}")
                    
                    # 데이터베이스 저장 단계
                    self.progress_updated.emit(i, total_files, f"💾 데이터베이스 저장 중: {filename}")
                    
                    if self.is_cancelled:
                        break
                    
                    try:
                        save_data = {
                            'subject': email_data['subject'],
                            'sender': email_data['sender'],
                            'sender_name': email_data['sender_name'],
                            'recipient': email_data['recipient'],
                            'recipient_name': email_data['recipient_name'],
                            'date_sent': email_data['date_sent'].isoformat() if isinstance(email_data['date_sent'], datetime) else email_data['date_sent'],
                            'date_received': email_data['date_received'].isoformat() if isinstance(email_data['date_received'], datetime) else email_data['date_received'],
                            'body_text': email_data['body_text'],
                            'body_html': email_data['body_html'],
                            'file_path': email_data['file_path'],
                            'file_size': email_data['file_size'],
                            'file_hash': email_data['file_hash'],
                            'ai_processed': email_data['ai_processed'],
                            'has_attachments': email_data['has_attachments'],
                            'attachment_count': email_data['attachment_count'],
                            'attachment_info': email_data['attachment_info']
                        }
                        email_id = self.storage_manager.save_email(save_data)
                        
                        # 태그 할당
                        if email_data['ai_processed'] and email_data.get('assigned_tags'):
                            assigned_tags = email_data['assigned_tags']
                            self.storage_manager.assign_tags_to_email(email_id, assigned_tags)
                            print(f"💾 태그 저장 완료: {assigned_tags}")
                        
                        # 저장된 이메일 다시 로드
                        saved_email = self.storage_manager.get_email_by_id(email_id)
                        if saved_email:
                            processed_emails.append(saved_email)
                            self.file_processed.emit(saved_email)
                        else:
                            processed_emails.append(email_data)
                            self.file_processed.emit(email_data)
                            
                    except Exception as db_error:
                        error_msg = f"{file_path}: 데이터베이스 저장 실패 - {str(db_error)}"
                        errors.append(error_msg)
                        print(f"DB 저장 오류: {error_msg}")
                        processed_emails.append(email_data)
                        self.file_processed.emit(email_data)
                    
                    # 완료 상태 업데이트
                    self.progress_updated.emit(i + 1, total_files, f"✅ 완료: {filename}")
                    
                except Exception as e:
                    error_msg = f"{file_path}: {str(e)}"
                    errors.append(error_msg)
                    print(f"파일 처리 오류: {error_msg}")
            
            # 처리 완료 신호
            if not self.is_cancelled:
                self.progress_updated.emit(total_files, total_files, "🎉 모든 파일 처리 완료!")
                self.processing_completed.emit(processed_emails, errors)
            
        except Exception as e:
            self.processing_error.emit(str(e))
    
    def cancel(self):
        """처리 취소"""
        self.is_cancelled = True


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""
    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_filter = {}
        self.settings = QSettings()
        self.current_worker = None  # 현재 실행 중인 워커 스레드 추적
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
            self.storage_manager = JSONStorageManager(self.file_manager.get_data_dir())
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
            self.tagger = Tagger(self.ollama_client, self.storage_manager)
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
        self.search_bar.setPlaceholderText("이메일 제목, 내용, 발신자, 수신자, 태그 검색...")
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
        
        # 검색 버튼 추가
        self.search_button = QPushButton("검색")
        self.search_button.setFixedHeight(32)
        self.search_button.setFixedWidth(60)
        self.search_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        self.search_button.clicked.connect(self.trigger_search)
        search_layout.addWidget(self.search_button)
        
        # 검색 초기화 버튼 추가
        self.clear_search_button = QPushButton("✕")
        self.clear_search_button.setFixedHeight(32)
        self.clear_search_button.setFixedWidth(32)
        self.clear_search_button.setToolTip("검색 초기화")
        self.clear_search_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        self.clear_search_button.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_search_button)
        
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
        
        # 이메일 뷰 (storage_manager 전달)
        self.email_view = EmailView(self.storage_manager)
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
        self.sidebar.refresh_requested.connect(self.refresh_all_data)  # 새로고침 버튼 연결
        self.email_view.status_changed.connect(self.statusBar().showMessage)
        
        # 이메일 뷰의 파일 처리 시그널 연결
        self.email_view.files_processing.connect(self.process_email_files)
        
        # 이메일 삭제 시그널 연결
        self.email_view.emails_deleted.connect(self.delete_emails)
        
        # 이메일 재분석 시그널 연결  
        self.email_view.reanalyze_requested.connect(self.reanalyze_email)
        
        # 검색바 시그널 연결 추가
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        self.search_bar.returnPressed.connect(self.trigger_search)

    def load_initial_data(self):
        self.load_tags()
        self.load_emails()

    def load_tags(self):
        try:
            # 저장소에서 실제 태그와 이메일 카운트 가져오기
            all_tags = self.storage_manager.get_all_tags()
            
            # 현재 로드된 이메일이 있으면 그것을 사용, 없으면 저장소에서 가져오기
            if hasattr(self, 'email_view') and hasattr(self.email_view, 'current_emails') and self.email_view.current_emails:
                emails = self.email_view.current_emails
                print(f"📊 [DEBUG] 캐시된 이메일 사용: {len(emails)}개")
            else:
                emails = self.storage_manager.get_emails(limit=1000)
                print(f"📊 [DEBUG] 저장소에서 이메일 로드: {len(emails)}개")
            
            # 태그별 이메일 카운트 계산 (개선된 로직)
            tag_counts = {}
            for email in emails:
                email_tags = email.get('tags', [])
                
                # 태그가 리스트인지 확인하고 처리
                if isinstance(email_tags, list):
                    for tag in email_tags:
                        if isinstance(tag, dict):
                            tag_name = tag.get('name', '')
                        else:
                            tag_name = str(tag)
                        
                        if tag_name:  # 빈 태그 이름 제외
                            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
                elif isinstance(email_tags, str) and email_tags:
                    # 단일 태그 문자열인 경우
                    tag_counts[email_tags] = tag_counts.get(email_tags, 0) + 1
            
            # 태그 데이터 구성
            tags_data = []
            for tag in all_tags:
                tag_name = tag.get('name', '')
                count = tag_counts.get(tag_name, 0)
                tags_data.append({
                    'name': tag_name,
                    'display_name': tag.get('display_name', tag_name),
                    'color': tag.get('color', '#007ACC'),
                    'count': count
                })
            
            # 카운트가 0인 태그도 표시하되, 실제 사용 중인 태그는 위로 정렬
            tags_data.sort(key=lambda x: (-x['count'], x['name']))
            
            self.sidebar.update_tags(tags_data)
            print(f"📊 태그 로드 완료: {[(t['name'], t['count']) for t in tags_data[:5]]}{'...' if len(tags_data) > 5 else ''}")
        except Exception as e:
            self.statusBar().showMessage(f"태그 로드 실패: {e}")
            import traceback
            traceback.print_exc()

    def load_emails(self):
        """데이터베이스에서 이메일 목록 로드"""
        try:
            emails_data = self.storage_manager.get_emails(limit=100)  # 이미 딕셔너리 형태로 반환됨
            
            # 디버깅: 로드된 이메일들의 ai_processed 상태 확인
            print(f"📧 [DEBUG] 데이터베이스에서 {len(emails_data)}개 이메일 로드됨")
            for i, email in enumerate(emails_data[:3]):  # 처음 3개만 출력
                print(f"   {i+1}. ID: {email.get('id', 'N/A')[:8]}...")
                print(f"      제목: {email.get('subject', 'N/A')[:30]}...")
                print(f"      ai_processed: {email.get('ai_processed', 'N/A')}")
                print(f"      tags: {email.get('tags', [])}")
            
            self.email_view.update_email_list(emails_data)
            self.statusBar().showMessage(f"{len(emails_data)}개 이메일 로드됨")
            
        except Exception as e:
            self.statusBar().showMessage(f"이메일 로드 실패: {e}")
            import traceback
            traceback.print_exc()

    def filter_by_tag(self, tag_name: str):
        """태그로 필터링"""
        try:
            print(f"🏷️ [DEBUG] 메인 윈도우에서 태그 필터링 요청: {tag_name}")
            
            # 현재 필터 상태 업데이트
            self.current_filter = {'tag': tag_name}
            
            # 최신 이메일 목록을 가져와서 필터링
            all_emails = self.storage_manager.get_emails(limit=1000)
            print(f"🏷️ [DEBUG] 필터링용 전체 이메일 로드: {len(all_emails)}개")
            
            # 이메일 뷰의 current_emails를 최신 상태로 업데이트
            self.email_view.current_emails = all_emails
            
            # 이메일 뷰에 필터링 요청
            self.email_view.filter_by_tag(tag_name)
            
            # 상태바 업데이트
            self.statusBar().showMessage(f"'{tag_name}' 태그로 필터링")
            
        except Exception as e:
            print(f"❌ 태그 필터링 요청 실패: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"태그 필터링 실패: {e}")

    def on_search_text_changed(self, text: str):
        """검색 텍스트가 변경될 때 호출 (실시간 검색을 위한 타이머 설정)"""
        # 기존 타이머가 있다면 중지
        if hasattr(self, 'search_timer'):
            self.search_timer.stop()
        
        # 새 타이머 생성 (500ms 후 검색 실행)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.trigger_search)
        self.search_timer.start(500)  # 500ms 지연

    def trigger_search(self):
        """검색 실행"""
        query = self.search_bar.text().strip()
        
        if query:
            # 검색 수행
            self.current_filter = {'search': query}
            self.statusBar().showMessage(f"'{query}' 검색 중...")
            
            try:
                # 저장소에서 검색 실행
                search_results = self.storage_manager.get_emails(
                    search_query=query,
                    limit=1000  # 검색 결과는 더 많이 표시
                )
                
                # 검색 결과를 이메일 뷰에 표시
                self.email_view.update_email_list(search_results)
                
                # 상태바에 검색 결과 표시
                result_count = len(search_results)
                if result_count > 0:
                    self.statusBar().showMessage(f"'{query}' 검색 완료: {result_count}개 이메일 발견", 3000)
                else:
                    self.statusBar().showMessage(f"'{query}' 검색 결과가 없습니다", 3000)
                    
                # 사이드바의 선택 해제 (검색 모드임을 표시)
                self.sidebar.clear_selection()
                
            except Exception as e:
                self.statusBar().showMessage(f"검색 중 오류 발생: {str(e)}", 5000)
                print(f"검색 오류: {e}")
        else:
            # 검색어가 없으면 전체 이메일 표시
            self.current_filter = {}
            self.statusBar().showMessage("검색 해제")
            self.load_emails()

    def clear_search(self):
        """검색 초기화"""
        self.search_bar.clear()
        self.current_filter = {}
        self.statusBar().showMessage("검색 초기화됨")
        self.load_emails()

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
            # 이전 워커가 실행 중이면 중단
            if self.current_worker and self.current_worker.isRunning():
                QMessageBox.warning(self, "처리 중", "이미 이메일 처리가 진행 중입니다. 완료 후 다시 시도해주세요.")
                return
            
            self.current_worker = EmailProcessingWorker(valid_files, {
                'file_manager': self.file_manager,
                'storage_manager': self.storage_manager,
                'tagger': self.tagger
            })
            
            # 시그널 연결
            self.current_worker.progress_updated.connect(self.email_view.show_processing_progress)
            self.current_worker.status_updated.connect(self.statusBar().showMessage)
            self.current_worker.processing_completed.connect(self.handle_processing_completed)
            self.current_worker.processing_error.connect(self.handle_processing_error)
            
            # 완료 시 워커 정리
            self.current_worker.finished.connect(self.cleanup_worker)
            
            self.current_worker.start()
            
        except ImportError as e:
            QMessageBox.critical(
                self,
                "모듈 오류",
                f"필요한 모듈을 가져올 수 없습니다:\n{str(e)}\n\n개발자에게 문의하세요."
            )
        except Exception as e:
            # 오류 발생 시 진행바 숨김
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
            self.tagger = Tagger(self.ollama_client, self.storage_manager)
            # ReplyGenerator 인스턴스 재생성 (set_client 대신)
            self.reply_generator = ReplyGenerator(self.ollama_client)
            self.statusBar().showMessage("Ollama 설정이 업데이트되었습니다.")
        except Exception as e:
            QMessageBox.warning(self, "오류", f"Ollama 클라이언트 재설정 중 오류 발생: {e}")

        # 태그 다시 로드
        self.load_tags()
        
    def refresh_all_data(self):
        """모든 데이터를 새로고침합니다."""
        self.load_tags()
        self.load_emails()
        self.statusBar().showMessage("데이터 새로고침 완료", 3000)

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
    
    def delete_emails(self, email_ids: List[int]):
        """이메일 삭제 처리"""
        try:
            if not email_ids:
                return
            
            # 데이터베이스에서 삭제
            result = self.storage_manager.delete_emails([str(email_id) for email_id in email_ids])
            
            success_count = result.get('success_count', 0)
            failed_count = result.get('failed_count', 0)
            
            if success_count > 0:
                # 이메일 목록과 태그 새로고침
                self.load_emails()
                self.load_tags()  # 태그 카운트 업데이트
                
                if failed_count > 0:
                    QMessageBox.warning(
                        self, 
                        "부분 삭제 완료",
                        f"총 {len(email_ids)}개 중 {success_count}개 삭제 완료, {failed_count}개 실패"
                    )
                    self.statusBar().showMessage(f"{success_count}개 이메일 삭제됨 ({failed_count}개 실패)")
                else:
                    self.statusBar().showMessage(f"{success_count}개 이메일 삭제됨")
            else:
                QMessageBox.critical(
                    self, 
                    "삭제 실패",
                    "선택한 이메일을 삭제할 수 없습니다."
                )
                self.statusBar().showMessage("이메일 삭제 실패")
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "삭제 오류",
                f"이메일 삭제 중 오류가 발생했습니다:\n{str(e)}"
            )
            self.statusBar().showMessage("이메일 삭제 오류")

    def reanalyze_email(self, email_data: Dict[str, Any]):
        """단일 이메일 재분석"""
        try:
            # Ollama 연결 상태 확인
            if not self.check_ollama_connection():
                self.statusBar().showMessage("Ollama 연결 실패 - 재분석이 중단되었습니다.", 5000)
                return
            
            email_id = email_data.get('id')
            if not email_id:
                QMessageBox.warning(self, "오류", "이메일 ID를 찾을 수 없습니다.")
                return
            
            self.statusBar().showMessage(f"재분석 중... '{email_data.get('subject', 'N/A')[:30]}...'")
            
            # AI 태깅 수행
            tagging_result = self.tagger.analyze_email(email_data)
            
            # 태깅 결과 처리
            if tagging_result is not None:
                # AI 분석 완료 (태그가 있든 없든)
                ai_processed = True
                assigned_tags = tagging_result if tagging_result else []
                tag_confidence = 1.0 if tagging_result else 0.5
                
                if tagging_result:
                    print(f"✅ 재분석 완료: {assigned_tags}")
                    message = f"재분석 완료: {len(assigned_tags)}개 태그 할당됨"
                else:
                    print(f"✅ 재분석 완료 - 해당 태그 없음")
                    message = "재분석 완료: 해당하는 태그 없음"
            else:
                # AI 분석 실패
                ai_processed = False
                assigned_tags = []
                tag_confidence = 0.0
                message = "재분석 실패: AI 오류"
                print(f"🚨 재분석 실패: {email_data.get('subject', 'N/A')}")
            
            # 데이터베이스 업데이트
            emails = self.storage_manager.get_emails(limit=1000)
            for i, email in enumerate(emails):
                if email.get('id') == email_id:
                    email['ai_processed'] = ai_processed
                    if ai_processed and assigned_tags:
                        # 기존 태그를 새 태그로 교체
                        email['tags'] = assigned_tags
                        # 스토리지에서 태그도 업데이트
                        self.storage_manager.assign_tags_to_email(email_id, assigned_tags)
                    break
            
            # UI 새로고침
            self.load_emails()
            self.load_tags()
            
            QMessageBox.information(self, "재분석 완료", message)
            self.statusBar().showMessage(message, 5000)
            
        except Exception as e:
            error_msg = f"재분석 중 오류 발생: {str(e)}"
            print(f"❌ {error_msg}")
            QMessageBox.critical(self, "재분석 오류", error_msg)
            self.statusBar().showMessage("재분석 실패", 5000)

    def handle_processing_completed(self, processed_emails, errors):
        """처리 완료 핸들러"""
        # 진행바 숨김 (2초 후)
        QTimer.singleShot(2000, self.email_view.hide_processing_progress)
        
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
                # 데이터베이스에서 전체 이메일 목록 다시 로드
                self.load_emails()
            
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

    def handle_processing_error(self, error_message):
        """처리 오류 핸들러"""
        # 진행바 즉시 숨김
        self.email_view.hide_processing_progress()
        QMessageBox.critical(self, "처리 오류", error_message)
        self.statusBar().showMessage("파일 처리 실패", 5000)

    def cleanup_worker(self):
        """워커 스레드 정리"""
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None

    def closeEvent(self, event):
        """애플리케이션 종료 시 안전한 스레드 정리"""
        if self.current_worker and self.current_worker.isRunning():
            # 사용자에게 확인
            reply = QMessageBox.question(
                self, 
                "처리 중", 
                "이메일 처리가 진행 중입니다. 종료하시겠습니까?\n처리 중인 작업이 중단됩니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 워커 스레드 취소 및 종료 대기
                self.current_worker.cancel()
                if not self.current_worker.wait(3000):  # 3초 대기
                    self.current_worker.terminate()  # 강제 종료
                    self.current_worker.wait()  # 종료 완료까지 대기
                self.current_worker.deleteLater()
                event.accept()
            else:
                event.ignore()
                return
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 