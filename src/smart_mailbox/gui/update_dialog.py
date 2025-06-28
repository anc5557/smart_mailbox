"""
업데이트 확인 및 버전 정보 다이얼로그
"""
import webbrowser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QProgressBar, QMessageBox, QTabWidget, QWidget,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette

from ..utils import UpdateChecker, VersionManager
from ..config.logger import logger


class UpdateCheckWorker(QThread):
    """백그라운드에서 업데이트 확인을 수행하는 워커 스레드"""
    
    update_checked = pyqtSignal(dict)  # 업데이트 확인 결과
    
    def __init__(self, update_checker: UpdateChecker):
        super().__init__()
        self.update_checker = update_checker
    
    def run(self):
        """업데이트 확인 실행"""
        result = self.update_checker.check_for_updates()
        self.update_checked.emit(result)


class AboutDialog(QDialog):
    """버전 정보 및 업데이트 확인 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.version_manager = VersionManager()
        self.update_checker = UpdateChecker()
        self.update_worker = None
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("Smart Mailbox 정보")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 버전 정보 탭
        version_tab = self.create_version_tab()
        tab_widget.addTab(version_tab, "🔍 버전 정보")
        
        # 업데이트 확인 탭
        update_tab = self.create_update_tab()
        tab_widget.addTab(update_tab, "🔄 업데이트 확인")
        
        layout.addWidget(tab_widget)
        
        # 닫기 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("닫기")
        self.close_btn.setMinimumWidth(80)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def create_version_tab(self) -> QWidget:
        """버전 정보 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 앱 제목
        title_label = QLabel("🏠 Smart Mailbox")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 설명
        desc_label = QLabel("AI 기반 이메일 자동 분석 및 답장 생성 데스크탑 애플리케이션")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 버전 정보 그리드
        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        
        version_info = self.version_manager.get_version_info()
        
        # 정보 항목들
        info_items = [
            ("애플리케이션 버전:", version_info['version']),
            ("Python 버전:", version_info['python_version']),
            ("플랫폼:", version_info['platform']),
            ("아키텍처:", version_info['architecture'])
        ]
        
        for i, (label_text, value_text) in enumerate(info_items):
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            
            value = QLabel(value_text)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            info_layout.addWidget(label, i, 0)
            info_layout.addWidget(value, i, 1)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # 저작권 정보
        copyright_label = QLabel("© 2024 Smart Mailbox Team. All rights reserved.")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(copyright_label)
        
        return widget
    
    def create_update_tab(self) -> QWidget:
        """업데이트 확인 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 현재 버전 정보
        current_version_layout = QHBoxLayout()
        current_version_layout.addWidget(QLabel("현재 버전:"))
        
        current_version = QLabel(self.version_manager.get_current_version())
        font = current_version.font()
        font.setBold(True)
        current_version.setFont(font)
        current_version_layout.addWidget(current_version)
        current_version_layout.addStretch()
        
        layout.addLayout(current_version_layout)
        
        # 업데이트 확인 버튼
        button_layout = QHBoxLayout()
        self.check_update_btn = QPushButton("🔄 업데이트 확인")
        self.check_update_btn.setMinimumHeight(35)
        self.check_update_btn.clicked.connect(self.check_for_updates)
        button_layout.addWidget(self.check_update_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 업데이트 정보 표시 영역
        self.update_info_widget = QWidget()
        self.update_info_layout = QVBoxLayout(self.update_info_widget)
        self.update_info_widget.setVisible(False)
        layout.addWidget(self.update_info_widget)
        
        layout.addStretch()
        
        return widget
    
    def setup_connections(self):
        """시그널 연결 설정"""
        pass
    
    def _open_url(self, url: str) -> None:
        """URL을 기본 브라우저에서 열기"""
        webbrowser.open(url)
    
    def check_for_updates(self):
        """업데이트 확인 시작"""
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("확인 중...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 무한 진행률
        self.update_info_widget.setVisible(False)
        
        # 기존 워커 정리
        if self.update_worker and self.update_worker.isRunning():
            self.update_worker.terminate()
            self.update_worker.wait()
        
        # 새 워커 시작
        self.update_worker = UpdateCheckWorker(self.update_checker)
        self.update_worker.update_checked.connect(self.on_update_checked)
        self.update_worker.start()
        
        # 타임아웃 타이머 (15초)
        QTimer.singleShot(15000, self.on_check_timeout)
    
    def on_update_checked(self, result: dict):
        """업데이트 확인 완료 처리"""
        self.check_update_btn.setEnabled(True)
        self.check_update_btn.setText("🔄 업데이트 확인")
        self.progress_bar.setVisible(False)
        
        # 기존 정보 위젯 내용 제거
        for i in reversed(range(self.update_info_layout.count())):
            widget = self.update_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        if result['success']:
            self.display_update_info(result)
        else:
            self.display_error_info(result)
        
        self.update_info_widget.setVisible(True)
    
    def display_update_info(self, result: dict):
        """업데이트 정보 표시"""
        if result['has_update']:
            # 새 버전 있음
            status_label = QLabel("🎉 새로운 버전이 있습니다!")
            status_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
            self.update_info_layout.addWidget(status_label)
            
            # 버전 정보
            version_layout = QHBoxLayout()
            version_layout.addWidget(QLabel("최신 버전:"))
            latest_version = QLabel(result['latest_version'])
            font = latest_version.font()
            font.setBold(True)
            latest_version.setFont(font)
            latest_version.setStyleSheet("color: #2ecc71;")
            version_layout.addWidget(latest_version)
            version_layout.addStretch()
            self.update_info_layout.addLayout(version_layout)
            
            # 릴리스 정보
            if result.get('release_name'):
                self.update_info_layout.addWidget(QLabel(f"릴리스: {result['release_name']}"))
            
            if result.get('published_date'):
                self.update_info_layout.addWidget(QLabel(f"발행일: {result['published_date']}"))
            
            # 릴리스 노트
            if result.get('release_notes'):
                notes_label = QLabel("새로운 기능:")
                notes_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
                self.update_info_layout.addWidget(notes_label)
                
                notes_text = QTextEdit()
                notes_text.setPlainText(result['release_notes'])
                notes_text.setMaximumHeight(100)
                notes_text.setReadOnly(True)
                self.update_info_layout.addWidget(notes_text)
            
            # 다운로드 버튼
            if result.get('download_url'):
                download_btn = QPushButton("📥 다운로드 페이지 열기")
                download_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                download_btn.clicked.connect(lambda: self._open_url(result['download_url']))
                self.update_info_layout.addWidget(download_btn)
        else:
            # 최신 버전 사용 중
            status_label = QLabel("✅ 최신 버전을 사용하고 있습니다!")
            status_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
            self.update_info_layout.addWidget(status_label)
            
            if result.get('latest_version'):
                version_label = QLabel(f"최신 버전: {result['latest_version']}")
                self.update_info_layout.addWidget(version_label)
    
    def display_error_info(self, result: dict):
        """오류 정보 표시"""
        status_label = QLabel("❌ 업데이트 확인 중 오류가 발생했습니다")
        status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        self.update_info_layout.addWidget(status_label)
        
        error_label = QLabel(f"오류: {result.get('error', '알 수 없는 오류')}")
        error_label.setStyleSheet("color: #e74c3c;")
        self.update_info_layout.addWidget(error_label)
        
        # 수동 확인 버튼
        manual_btn = QPushButton("🌐 GitHub에서 수동 확인")
        manual_btn.clicked.connect(lambda: self._open_url("https://github.com/anc5557/smart_mailbox/releases"))
        self.update_info_layout.addWidget(manual_btn)
    
    def on_check_timeout(self):
        """업데이트 확인 타임아웃 처리"""
        if self.update_worker and self.update_worker.isRunning():
            self.update_worker.terminate()
            self.update_worker.wait()
            
            self.check_update_btn.setEnabled(True)
            self.check_update_btn.setText("🔄 업데이트 확인")
            self.progress_bar.setVisible(False)
            
            QMessageBox.warning(
                self, 
                "타임아웃", 
                "업데이트 확인이 시간 초과되었습니다.\n네트워크 연결을 확인해주세요."
            )
    
    def closeEvent(self, event):
        """다이얼로그 닫기 이벤트"""
        # 실행 중인 워커 정리
        if self.update_worker and self.update_worker.isRunning():
            self.update_worker.terminate()
            self.update_worker.wait()
        
        super().closeEvent(event) 