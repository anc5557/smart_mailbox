"""
AI Smart Mailbox 메인 윈도우
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QStatusBar, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon

from .sidebar import Sidebar
from .email_view import EmailView
from .settings import SettingsDialog


class MainWindow(QMainWindow):
    """메인 애플리케이션 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu()
        
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("AI Smart Mailbox")
        self.setMinimumSize(QSize(1200, 800))
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 수평 분할기 생성
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 사이드바 생성
        self.sidebar = Sidebar()
        self.sidebar.setMaximumWidth(250)
        self.sidebar.setMinimumWidth(200)
        splitter.addWidget(self.sidebar)
        
        # 이메일 뷰 생성
        self.email_view = EmailView()
        splitter.addWidget(self.email_view)
        
        # 분할기 비율 설정 (사이드바 20%, 메인 80%)
        splitter.setSizes([200, 1000])
        
        # 상태바 설정
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비됨")
        
        # 시그널 연결
        self.connect_signals()
        
        # 데이터베이스 초기화
        self.init_database()
        
    def setup_menu(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")
        
        open_action = QAction("이메일 파일 열기(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_email_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close_application)
        file_menu.addAction(exit_action)
        
        # 설정 메뉴
        settings_menu = menubar.addMenu("설정(&S)")
        
        preferences_action = QAction("환경설정(&P)", self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
        ollama_settings_action = QAction("Ollama 설정(&O)", self)
        ollama_settings_action.triggered.connect(self.show_ollama_settings)
        settings_menu.addAction(ollama_settings_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")
        
        about_action = QAction("정보(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def connect_signals(self):
        """시그널 연결"""
        # 사이드바에서 태그 선택시 이메일 뷰 업데이트
        self.sidebar.tag_selected.connect(self.email_view.filter_by_tag)
        
        # 이메일 뷰에서 상태 업데이트시 상태바 변경
        self.email_view.status_changed.connect(self.status_bar.showMessage)
        
        # 이메일 처리 요청 시그널 연결
        self.email_view.email_processing_requested.connect(self.process_emails)
        
    def open_email_file(self):
        """이메일 파일 열기"""
        # TODO: 파일 대화상자 구현
        self.status_bar.showMessage("이메일 파일 열기 기능 구현 예정")
        
    def show_preferences(self):
        """환경설정 창 표시"""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self.on_settings_changed)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self.status_bar.showMessage("설정이 저장되었습니다")
        
    def show_ollama_settings(self):
        """Ollama 설정 창 표시"""
        dialog = SettingsDialog(self)
        # Ollama 탭으로 이동
        dialog.settings_changed.connect(self.on_settings_changed)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self.status_bar.showMessage("Ollama 설정이 저장되었습니다")
            
    def on_settings_changed(self, settings: dict):
        """설정 변경 시 처리"""
        # TODO: 설정을 파일에 저장하고 애플리케이션에 적용
        print("설정 변경됨:", settings)
        self.status_bar.showMessage("설정이 적용되었습니다")
        
    def close_application(self):
        """애플리케이션 종료"""
        self.close()
        
    def show_about(self):
        """정보 창 표시"""
        # TODO: 정보 창 구현
        self.status_bar.showMessage("정보 창 구현 예정")
    
    def init_database(self):
        """데이터베이스 초기화"""
        from ..storage.database import DatabaseManager
        try:
            self.db_manager = DatabaseManager()
            self.status_bar.showMessage("데이터베이스 초기화 완료")
            
            # 태그 목록 업데이트
            self.load_tags()
        except Exception as e:
            self.status_bar.showMessage(f"데이터베이스 초기화 실패: {e}")
    
    def load_tags(self):
        """태그 목록 로드"""
        try:
            tags = self.db_manager.get_all_tags()
            tags_data = []
            
            for tag in tags:
                # 태그별 이메일 개수 계산
                emails = self.db_manager.get_emails_by_tag(getattr(tag, 'name'))
                tag_data = {
                    'name': getattr(tag, 'name'),
                    'display_name': getattr(tag, 'display_name'),
                    'color': getattr(tag, 'color'),
                    'is_system': getattr(tag, 'is_system'),
                    'count': len(emails)
                }
                tags_data.append(tag_data)
            
            self.sidebar.update_tags(tags_data)
        except Exception as e:
            self.status_bar.showMessage(f"태그 로드 실패: {e}")
    
    def process_emails(self, file_paths: list):
        """이메일 파일들 처리"""
        from ..ai.tagger import EmailTaggingManager
        from ..email.parser import EmailParser
        
        try:
            self.status_bar.showMessage(f"{len(file_paths)}개 파일 처리 중...")
            
            # 이메일 파서 초기화
            parser = EmailParser()
            
            # AI 태깅 매니저 초기화
            tagging_manager = EmailTaggingManager(self.db_manager)
            
            processed_count = 0
            for file_path in file_paths:
                try:
                    # 이메일 파싱
                    email_data = parser.parse_eml_file(file_path)
                    
                    # 데이터베이스에 저장
                    email_id = self.db_manager.save_email(email_data)
                    
                    # AI 자동 태깅
                    result = tagging_manager.process_email(email_id)
                    
                    if result['status'] == 'success':
                        processed_count += 1
                        
                except Exception as e:
                    self.status_bar.showMessage(f"파일 처리 실패: {file_path} - {e}")
            
            self.status_bar.showMessage(f"처리 완료: {processed_count}/{len(file_paths)}개")
            
            # 화면 새로고침
            self.load_tags()
            self.load_emails()
            
        except Exception as e:
            self.status_bar.showMessage(f"이메일 처리 실패: {e}")
    
    def load_emails(self):
        """이메일 목록 로드"""
        try:
            emails = self.db_manager.get_all_emails(limit=50)
            emails_data = []
            
            for email in emails:
                email_data = {
                    'id': getattr(email, 'id'),
                    'subject': getattr(email, 'subject'),
                    'sender': getattr(email, 'sender'),
                    'sender_name': getattr(email, 'sender_name'),
                    'recipient': getattr(email, 'recipient'),
                    'recipient_name': getattr(email, 'recipient_name'),
                    'date_sent': getattr(email, 'date_sent'),
                    'has_attachments': getattr(email, 'has_attachments'),
                    'ai_processed': getattr(email, 'ai_processed'),
                    'tags': [getattr(tag, 'display_name') for tag in email.tags]
                }
                emails_data.append(email_data)
            
            self.email_view.update_email_list(emails_data)
        except Exception as e:
            self.status_bar.showMessage(f"이메일 로드 실패: {e}")


def main():
    """GUI 애플리케이션 실행"""
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI Smart Mailbox")
    app.setApplicationVersion("0.1.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 