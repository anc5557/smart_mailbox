"""
AI Smart Mailbox 이메일 뷰
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextEdit, QPushButton, QProgressBar, QFrame,
    QSplitter, QGroupBox, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QThread, QTimer, QSettings
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class EmailDetailWidget(QWidget):
    """이메일 상세 보기 위젯"""
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.setup_ui()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 헤더 정보 (제목, 발신자, 날짜)
        self.setup_header(layout)
        
        # 태그 정보
        self.setup_tags_section(layout)
        
        # 이메일 본문
        self.setup_body_section(layout)
        
        # 첨부파일 정보
        self.setup_attachments_section(layout)
        
        # 액션 버튼들
        self.setup_actions_section(layout)
        
        # 기본적으로 숨김
        self.hide()
    
    def setup_header(self, layout: QVBoxLayout):
        """헤더 섹션 설정"""
        self.header_group = QGroupBox("이메일 정보")
        header_layout = QVBoxLayout(self.header_group)
        
        # 제목
        self.subject_label = QLabel()
        self.subject_label.setWordWrap(True)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.subject_label.setFont(font)
        header_layout.addWidget(self.subject_label)
        
        # 발신자
        self.sender_label = QLabel()
        self.sender_label.setWordWrap(True)
        header_layout.addWidget(self.sender_label)
        
        # 날짜
        self.date_label = QLabel()
        header_layout.addWidget(self.date_label)
        
        layout.addWidget(self.header_group)
    
    def setup_tags_section(self, layout: QVBoxLayout):
        """태그 섹션 설정"""
        self.tags_group = QGroupBox("AI 분석 태그")
        tags_layout = QVBoxLayout(self.tags_group)
        
        self.tags_label = QLabel("분석 중...")
        tags_layout.addWidget(self.tags_label)
        
        # 기본적으로 숨김
        self.tags_group.hide()
        
        layout.addWidget(self.tags_group)
    
    def setup_body_section(self, layout: QVBoxLayout):
        """본문 섹션 설정"""
        self.body_group = QGroupBox("이메일 본문")
        body_layout = QVBoxLayout(self.body_group)
        
        # 본문 텍스트
        self.body_text = QTextEdit()
        self.body_text.setReadOnly(True)
        body_layout.addWidget(self.body_text)
        
        layout.addWidget(self.body_group)
    
    def setup_attachments_section(self, layout: QVBoxLayout):
        """첨부파일 섹션 설정"""
        self.attachments_group = QGroupBox("첨부파일")
        attachments_layout = QVBoxLayout(self.attachments_group)
        
        self.attachments_label = QLabel("첨부파일이 없습니다.")
        attachments_layout.addWidget(self.attachments_label)
        
        # 기본적으로 숨김
        self.attachments_group.hide()
        
        layout.addWidget(self.attachments_group)
    
    def setup_actions_section(self, layout: QVBoxLayout):
        """액션 버튼 섹션 설정"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        
        # AI 답장 생성 버튼
        self.generate_reply_button = QPushButton("🤖 AI 답장 생성")
        actions_layout.addWidget(self.generate_reply_button)
        
        # 재분석 버튼
        self.reanalyze_button = QPushButton("🔄 재분석")
        actions_layout.addWidget(self.reanalyze_button)
        
        actions_layout.addStretch()
        layout.addWidget(actions_widget)
    
    def update_email(self, email_data: Dict[str, Any]):
        """이메일 데이터로 UI 업데이트"""
        self.current_email = email_data
        
        # 헤더 정보 업데이트
        self.subject_label.setText(f"제목: {email_data.get('subject', 'N/A')}")
        self.sender_label.setText(f"발신자: {email_data.get('from', 'N/A')}")
        self.date_label.setText(f"날짜: {email_data.get('date', 'N/A')}")
        
        # 본문 업데이트
        self.body_text.setPlainText(email_data.get('body', '본문이 없습니다.'))
        
        # 태그 정보 업데이트
        tags = email_data.get('tags', [])
        if tags:
            tags_text = ', '.join([f"#{tag}" for tag in tags])
            self.tags_label.setText(tags_text)
            self.tags_group.show()
        else:
            self.tags_label.setText("분석 중...")
            self.tags_group.hide()
        
        # 첨부파일 정보 업데이트
        attachments = email_data.get('attachments', [])
        if attachments:
            attachment_names = [att.get('name', 'Unknown') for att in attachments]
            self.attachments_label.setText('\n'.join(attachment_names))
            self.attachments_group.show()
        else:
            self.attachments_label.setText("첨부파일이 없습니다.")
            self.attachments_group.hide()
        
        self.show()
    
    def clear(self):
        """상세 정보 초기화"""
        self.current_email = None
        self.subject_label.setText("")
        self.sender_label.setText("")
        self.date_label.setText("")
        self.body_text.clear()
        self.tags_label.setText("분석 중...")
        self.tags_group.hide()
        self.attachments_label.setText("첨부파일이 없습니다.")
        self.attachments_group.hide()
        self.hide()


class EmailListItem(QListWidgetItem):
    """이메일 목록 아이템"""
    
    def __init__(self, email_data: Dict[str, Any]):
        super().__init__()
        self.email_data = email_data
        self.setup_item()
    
    def setup_item(self):
        """아이템 설정"""
        subject = self.email_data.get('subject', 'No Subject')
        sender = self.email_data.get('from', 'Unknown Sender')
        date = self.email_data.get('date', 'Unknown Date')
        
        # 날짜 포맷팅
        try:
            if isinstance(date, str) and date != 'Unknown Date':
                parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_date = str(date)
        except:
            formatted_date = str(date)
        
        # 텍스트 설정
        display_text = f"📧 {subject}\n👤 {sender}\n📅 {formatted_date}"
        self.setText(display_text)


class EmailListWidget(QListWidget):
    """드래그 앤 드롭 지원 이메일 목록"""
    
    files_dropped = pyqtSignal(list)  # 드롭된 파일 목록
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """드래그 이동 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.eml'):
                    file_paths.append(file_path)
            
            if file_paths:
                self.files_dropped.emit(file_paths)
            
            event.acceptProposedAction()


class EmailView(QWidget):
    """메인 이메일 뷰"""
    
    status_changed = pyqtSignal(str)
    files_processing = pyqtSignal(list)  # 파일 처리 요청 시그널
    
    def __init__(self):
        super().__init__()
        self.current_emails = []
        self.setup_ui()
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 왼쪽: 이메일 목록
        self.setup_email_list(splitter)
        
        # 오른쪽: 이메일 상세 정보
        self.email_detail = EmailDetailWidget()
        splitter.addWidget(self.email_detail)
        
        # 스플리터 비율 설정 (목록:상세 = 1:2)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
    
    def setup_email_list(self, splitter: QSplitter):
        """이메일 목록 영역 설정"""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        # 제목
        self.list_title = QLabel("📧 전체 이메일")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.list_title.setFont(font)
        self.list_title.setStyleSheet("padding: 10px;")
        list_layout.addWidget(self.list_title)
        
        # 이메일 목록
        self.email_list = EmailListWidget()
        self.email_list.itemClicked.connect(self.on_email_selected)
        self.email_list.files_dropped.connect(self.on_files_dropped)
        list_layout.addWidget(self.email_list)
        
        # 파일 업로드 버튼
        self.upload_button = QPushButton("📁 이메일 파일 선택")
        self.upload_button.clicked.connect(self.on_upload_clicked)
        list_layout.addWidget(self.upload_button)
        
        # 프로그레스 바 (기본적으로 숨김)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        list_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(list_widget)
    
    def show_home_view(self):
        """홈 뷰 표시"""
        self.list_title.setText("📧 전체 이메일")
        self.email_detail.clear()
        self.update_email_list([])
        self.status_changed.emit("홈 화면")
    
    def filter_by_tag(self, tag_name: str):
        """태그로 이메일 필터링"""
        # TODO: 데이터베이스에서 해당 태그의 이메일 조회
        self.list_title.setText(f"🏷️ {tag_name} 태그")
        self.email_detail.clear()
        self.status_changed.emit(f"'{tag_name}' 태그로 필터링됨")
    
    def update_email_list(self, emails_data: List[Dict[str, Any]]):
        """이메일 목록 업데이트"""
        self.current_emails = emails_data
        self.email_list.clear()
        
        if not emails_data:
            # 빈 상태 표시
            empty_item = QListWidgetItem("📥 이메일이 없습니다.\n\n.eml 파일을 드래그 앤 드롭하거나\n'이메일 파일 선택' 버튼을 클릭하세요.")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.email_list.addItem(empty_item)
        else:
            for email_data in emails_data:
                item = EmailListItem(email_data)
                self.email_list.addItem(item)
    
    def on_email_selected(self, item: QListWidgetItem):
        """이메일 선택 이벤트"""
        if isinstance(item, EmailListItem):
            self.email_detail.update_email(item.email_data)
            self.status_changed.emit(f"이메일 선택: {item.email_data.get('subject', 'N/A')}")
    
    def on_upload_clicked(self):
        """파일 업로드 버튼 클릭"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "이메일 파일 선택", "", "이메일 파일 (*.eml);;모든 파일 (*.*)"
        )
        if file_paths:
            self.on_files_dropped(file_paths)
    
    def on_files_dropped(self, file_paths: List[str]):
        """파일 드롭 처리"""
        valid_files = [path for path in file_paths if path.endswith('.eml')]
        if valid_files:
            self.status_changed.emit(f"{len(valid_files)}개 이메일 파일 선택됨 - Ollama 연결 확인 중...")
            # 메인 윈도우로 파일 처리 요청 전달 (Ollama 연결 확인 포함)
            self.files_processing.emit(valid_files)
        else:
            QMessageBox.warning(self, "경고", "유효한 .eml 파일이 없습니다.")
    
    def show_processing_progress(self, current: int, total: int):
        """처리 진행률 표시"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.show()
        self.status_changed.emit(f"이메일 처리 중... ({current}/{total})")
    
    def hide_processing_progress(self):
        """처리 진행률 숨김"""
        self.progress_bar.hide()
    
    def show_processing_error(self, error_message: str):
        """처리 오류 표시"""
        self.progress_bar.hide()
        QMessageBox.critical(self, "오류", f"이메일 처리 중 오류가 발생했습니다:\n{error_message}")
        self.status_changed.emit("처리 실패") 