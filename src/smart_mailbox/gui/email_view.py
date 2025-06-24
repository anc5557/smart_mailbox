"""
AI Smart Mailbox 이메일 뷰
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextEdit, QPushButton, QProgressBar, QFrame,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette


class DragDropArea(QFrame):
    """드래그 앤 드롭 영역"""
    
    files_dropped = pyqtSignal(list)  # 파일이 드롭되었을 때
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 아이콘 (텍스트로 대체)
        icon_label = QLabel("📧")
        icon_font = QFont()
        icon_font.setPointSize(48)
        icon_label.setFont(icon_font)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # 메인 텍스트
        main_label = QLabel("이메일 파일(.eml)을 여기에 드래그하세요")
        main_font = QFont()
        main_font.setPointSize(16)
        main_font.setBold(True)
        main_label.setFont(main_font)
        main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_label)
        
        # 서브 텍스트
        sub_label = QLabel("또는 파일 메뉴에서 '이메일 파일 열기'를 선택하세요")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet("color: #666;")
        layout.addWidget(sub_label)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            # .eml 파일 검사
            urls = event.mimeData().urls()
            eml_files = [url.toLocalFile() for url in urls 
                        if url.toLocalFile().lower().endswith('.eml')]
            if eml_files:
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QFrame {
                        border: 2px solid #0078d4;
                        border-radius: 10px;
                        background-color: #e3f2fd;
                    }
                """)
                
    def dragLeaveEvent(self, event):
        """드래그 나감 이벤트"""
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
            }
            QFrame:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        urls = event.mimeData().urls()
        eml_files = [url.toLocalFile() for url in urls 
                    if url.toLocalFile().lower().endswith('.eml')]
        
        if eml_files:
            self.files_dropped.emit(eml_files)
            event.acceptProposedAction()
            
        # 스타일 초기화
        self.dragLeaveEvent(None)


class EmailListView(QWidget):
    """이메일 목록 뷰"""
    
    email_selected = pyqtSignal(dict)  # 이메일이 선택되었을 때
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 헤더
        header_layout = QHBoxLayout()
        
        title_label = QLabel("이메일 목록")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 새로고침 버튼
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh_emails)
        header_layout.addWidget(refresh_button)
        
        layout.addLayout(header_layout)
        
        # 분할기
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # 이메일 목록
        self.email_list = QListWidget()
        self.email_list.setAlternatingRowColors(True)
        self.email_list.itemClicked.connect(self.on_email_selected)
        splitter.addWidget(self.email_list)
        
        # 이메일 미리보기
        preview_group = QGroupBox("미리보기")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlainText("이메일을 선택하면 내용이 표시됩니다.")
        preview_layout.addWidget(self.preview_text)
        
        splitter.addWidget(preview_group)
        
        # 분할기 비율 설정
        splitter.setSizes([400, 300])
        
    def on_email_selected(self, item: QListWidgetItem):
        """이메일 선택 이벤트"""
        email_data = item.data(Qt.ItemDataRole.UserRole)
        if email_data:
            self.email_selected.emit(email_data)
            self.update_preview(email_data)
            
    def update_preview(self, email_data: dict):
        """미리보기 업데이트"""
        preview_text = f"""
발신자: {email_data.get('sender', 'N/A')}
수신자: {email_data.get('recipient', 'N/A')}
제목: {email_data.get('subject', 'N/A')}
날짜: {email_data.get('date', 'N/A')}
태그: {', '.join(email_data.get('tags', []))}

--- 본문 ---
{email_data.get('body', 'N/A')}
        """.strip()
        
        self.preview_text.setPlainText(preview_text)
        
    def add_email(self, email_data: dict):
        """이메일 추가"""
        display_text = f"{email_data.get('subject', 'No Subject')} - {email_data.get('sender', 'Unknown')}"
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, email_data)
        self.email_list.addItem(item)
        
    def clear_emails(self):
        """이메일 목록 지우기"""
        self.email_list.clear()
        self.preview_text.setPlainText("이메일을 선택하면 내용이 표시됩니다.")
        
    def refresh_emails(self):
        """이메일 새로고침"""
        # TODO: 데이터베이스에서 이메일 다시 로드
        print("이메일 새로고침 기능 구현 예정")


class EmailView(QWidget):
    """메인 이메일 뷰 위젯"""
    
    status_changed = pyqtSignal(str)  # 상태 변경 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tag = "home"
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 스택 위젯으로 홈/목록 뷰 전환
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # 홈 뷰 (드래그 앤 드롭)
        self.home_view = self.create_home_view()
        self.stacked_widget.addWidget(self.home_view)
        
        # 이메일 목록 뷰
        self.list_view = EmailListView()
        self.stacked_widget.addWidget(self.list_view)
        
        # 시그널 연결
        self.connect_signals()
        
    def create_home_view(self) -> QWidget:
        """홈 뷰 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 드래그 앤 드롭 영역
        self.drag_drop_area = DragDropArea()
        layout.addWidget(self.drag_drop_area)
        
        # 진행 상황 섹션
        progress_group = QGroupBox("처리 진행 상황")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("대기 중...")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        return widget
        
    def connect_signals(self):
        """시그널 연결"""
        self.drag_drop_area.files_dropped.connect(self.process_email_files)
        self.list_view.email_selected.connect(self.on_email_selected)
        
    def filter_by_tag(self, tag: str):
        """태그별 필터링"""
        self.current_tag = tag
        
        if tag == "home":
            self.stacked_widget.setCurrentWidget(self.home_view)
            self.status_changed.emit("홈 화면")
        else:
            self.stacked_widget.setCurrentWidget(self.list_view)
            self.load_emails_by_tag(tag)
            self.status_changed.emit(f"태그 '{tag}' 필터 적용됨")
            
    def load_emails_by_tag(self, tag: str):
        """태그별 이메일 로드"""
        # TODO: 데이터베이스에서 태그별 이메일 로드
        self.list_view.clear_emails()
        
        # 임시 데이터
        if tag == "important":
            sample_email = {
                'subject': '중요한 회의 안내',
                'sender': 'boss@company.com',
                'recipient': 'me@company.com',
                'date': '2024-01-15',
                'tags': ['important'],
                'body': '내일 오후 2시에 중요한 회의가 있습니다.'
            }
            self.list_view.add_email(sample_email)
            
    def process_email_files(self, file_paths: list):
        """이메일 파일 처리"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(file_paths))
        self.progress_bar.setValue(0)
        
        for i, file_path in enumerate(file_paths):
            self.progress_label.setText(f"처리 중: {file_path}")
            # TODO: 실제 .eml 파일 파싱 및 AI 분석
            self.progress_bar.setValue(i + 1)
            
        self.progress_label.setText(f"{len(file_paths)}개 파일 처리 완료")
        self.status_changed.emit(f"{len(file_paths)}개 이메일 파일 처리 완료")
        
        # 3초 후 진행바 숨기기
        # TODO: QTimer 사용하여 개선
        
    def on_email_selected(self, email_data: dict):
        """이메일 선택 이벤트"""
        subject = email_data.get('subject', 'No Subject')
        self.status_changed.emit(f"선택됨: {subject}") 