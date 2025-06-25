"""
AI Smart Mailbox 이메일 뷰
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextEdit, QPushButton, QProgressBar, QFrame,
    QSplitter, QGroupBox, QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QThread, QTimer
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class EmailListItem(QListWidgetItem):
    """이메일 목록 아이템"""
    
    def __init__(self, email_data: Dict[str, Any]):
        super().__init__()
        self.email_data = email_data
        self.setup_item()
    
    def setup_item(self):
        """아이템 설정"""
        # 제목과 발신자 정보 표시
        subject = self.email_data.get("subject", "제목 없음")
        sender = self.email_data.get("sender", "알 수 없음")
        sender_name = self.email_data.get("sender_name")
        
        if sender_name:
            sender_display = f"{sender_name} <{sender}>"
        else:
            sender_display = sender
        
        # 날짜 포맷팅
        date_sent = self.email_data.get("date_sent")
        if isinstance(date_sent, datetime):
            date_str = date_sent.strftime("%Y-%m-%d %H:%M")
        else:
            date_str = "날짜 불명"
        
        # 첨부파일 표시
        attachment_indicator = "📎 " if self.email_data.get("has_attachments", False) else ""
        
        # AI 처리 상태 표시
        ai_indicator = "🤖 " if self.email_data.get("ai_processed", False) else "⏳ "
        
        # 표시 텍스트 구성
        display_text = f"{ai_indicator}{attachment_indicator}{subject}\n👤 {sender_display}\n📅 {date_str}"
        
        self.setText(display_text)
        
        # 스타일 적용
        if not self.email_data.get("ai_processed", False):
            # 미처리 이메일은 흐릿하게
            self.setForeground(QColor("#888"))
        
        # 데이터 저장
        self.setData(Qt.ItemDataRole.UserRole, self.email_data)


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
        """헤더 영역 설정"""
        header_group = QGroupBox("이메일 정보")
        header_layout = QVBoxLayout(header_group)
        
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
        self.sender_label.setStyleSheet("color: #666; margin: 5px 0px;")
        header_layout.addWidget(self.sender_label)
        
        # 수신자
        self.recipient_label = QLabel()
        self.recipient_label.setStyleSheet("color: #666; margin: 5px 0px;")
        header_layout.addWidget(self.recipient_label)
        
        # 날짜
        self.date_label = QLabel()
        self.date_label.setStyleSheet("color: #666; margin: 5px 0px;")
        header_layout.addWidget(self.date_label)
        
        layout.addWidget(header_group)
    
    def setup_tags_section(self, layout: QVBoxLayout):
        """태그 섹션 설정"""
        self.tags_group = QGroupBox("태그")
        tags_layout = QHBoxLayout(self.tags_group)
        
        self.tags_container = QWidget()
        self.tags_container_layout = QHBoxLayout(self.tags_container)
        self.tags_container_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.addWidget(self.tags_container)
        
        layout.addWidget(self.tags_group)
    
    def setup_body_section(self, layout: QVBoxLayout):
        """본문 섹션 설정"""
        body_group = QGroupBox("이메일 내용")
        body_layout = QVBoxLayout(body_group)
        
        self.body_text = QTextEdit()
        self.body_text.setReadOnly(True)
        self.body_text.setMinimumHeight(200)
        body_layout.addWidget(self.body_text)
        
        layout.addWidget(body_group)
    
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
        self.generate_reply_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        actions_layout.addWidget(self.generate_reply_button)
        
        # 재분석 버튼
        self.reanalyze_button = QPushButton("🔄 재분석")
        self.reanalyze_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        actions_layout.addWidget(self.reanalyze_button)
        
        actions_layout.addStretch()
        layout.addWidget(actions_widget)
    
    def show_email(self, email_data: Dict[str, Any], tags_data: Optional[List[Dict[str, Any]]] = None):
        """이메일 상세 정보 표시"""
        self.current_email = email_data
        
        # 헤더 정보 업데이트
        subject = email_data.get("subject", "제목 없음")
        self.subject_label.setText(subject)
        
        sender = email_data.get("sender", "")
        sender_name = email_data.get("sender_name", "")
        if sender_name:
            sender_display = f"📤 발신자: {sender_name} <{sender}>"
        else:
            sender_display = f"📤 발신자: {sender}"
        self.sender_label.setText(sender_display)
        
        recipient = email_data.get("recipient", "")
        recipient_name = email_data.get("recipient_name", "")
        if recipient_name:
            recipient_display = f"📥 수신자: {recipient_name} <{recipient}>"
        else:
            recipient_display = f"📥 수신자: {recipient}"
        self.recipient_label.setText(recipient_display)
        
        # 날짜 정보
        date_sent = email_data.get("date_sent")
        if isinstance(date_sent, datetime):
            date_str = date_sent.strftime("%Y년 %m월 %d일 %H:%M")
        else:
            date_str = "날짜 불명"
        self.date_label.setText(f"📅 날짜: {date_str}")
        
        # 태그 정보 업데이트
        self.update_tags_display(tags_data if tags_data is not None else [])
        
        # 본문 내용
        body_text = email_data.get("body_text", "")
        body_html = email_data.get("body_html", "")
        
        if body_text:
            self.body_text.setPlainText(body_text)
        elif body_html:
            self.body_text.setHtml(body_html)
        else:
            self.body_text.setPlainText("이메일 내용을 표시할 수 없습니다.")
        
        # 첨부파일 정보
        if email_data.get("has_attachments", False):
            attachment_count = email_data.get("attachment_count", 0)
            self.attachments_label.setText(f"첨부파일 {attachment_count}개")
            self.attachments_group.show()
        else:
            self.attachments_group.hide()
        
        # 액션 버튼 상태 업데이트
        ai_processed = email_data.get("ai_processed", False)
        
        # 회신필요 태그가 있는지 확인
        has_reply_needed = any(tag.get("name") == "reply_needed" for tag in tags_data or [])
        self.generate_reply_button.setEnabled(ai_processed and has_reply_needed)
        
        # 위젯 표시
        self.show()
    
    def update_tags_display(self, tags_data: List[Dict[str, Any]]):
        """태그 표시 업데이트"""
        # 기존 태그 위젯 제거
        for i in reversed(range(self.tags_container_layout.count())):
            child = self.tags_container_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        if not tags_data:
            no_tags_label = QLabel("태그 없음")
            no_tags_label.setStyleSheet("color: #888; font-style: italic;")
            self.tags_container_layout.addWidget(no_tags_label)
        else:
            for tag_data in tags_data:
                tag_widget = self.create_tag_widget(tag_data)
                self.tags_container_layout.addWidget(tag_widget)
        
        self.tags_container_layout.addStretch()
    
    def create_tag_widget(self, tag_data: Dict[str, Any]) -> QWidget:
        """태그 위젯 생성"""
        tag_widget = QLabel(tag_data.get("display_name", tag_data.get("name", "")))
        tag_widget.setStyleSheet(f"""
            QLabel {{
                background-color: {tag_data.get('color', '#007ACC')};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                margin: 2px;
            }}
        """)
        return tag_widget
    
    def clear(self):
        """표시 내용 초기화"""
        self.current_email = None
        self.hide()


class EmailListWidget(QListWidget):
    """드래그 앤 드롭 지원 이메일 목록"""
    
    files_dropped = pyqtSignal(list)  # 드롭된 파일 목록
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setup_styling()
    
    def setup_styling(self):
        """스타일링 설정"""
        self.setStyleSheet("""
            QListWidget {
                background-color: #fafafa;
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 20px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
                border-color: #2196f3;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border-color: #2196f3;
            }
        """)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QListWidget {
                    background-color: #e8f5e8;
                    border: 2px dashed #4CAF50;
                    border-radius: 10px;
                    padding: 20px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        """드래그 이탈 이벤트"""
        self.setup_styling()
    
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        self.setup_styling()
        
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.eml'):
                    file_paths.append(file_path)
            
            if file_paths:
                self.files_dropped.emit(file_paths)
            
            event.acceptProposedAction()


class EmailView(QWidget):
    """이메일 메인 뷰"""
    
    status_changed = pyqtSignal(str)  # 상태 변경 신호
    email_processing_requested = pyqtSignal(list)  # 이메일 처리 요청
    
    def __init__(self):
        super().__init__()
        self.current_emails = []
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 수평 분할기 (목록 + 상세)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 왼쪽: 이메일 목록
        self.setup_email_list(splitter)
        
        # 오른쪽: 이메일 상세
        self.email_detail = EmailDetailWidget()
        splitter.addWidget(self.email_detail)
        
        # 분할기 비율 설정 (목록 40%, 상세 60%)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
        # 기본 상태 표시
        self.show_home_view()
    
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
        list_layout.addWidget(self.list_title)
        
        # 이메일 목록
        self.email_list = EmailListWidget()
        self.email_list.itemClicked.connect(self.on_email_selected)
        self.email_list.files_dropped.connect(self.on_files_dropped)
        list_layout.addWidget(self.email_list)
        
        # 파일 업로드 버튼
        self.upload_button = QPushButton("📁 이메일 파일 선택")
        self.upload_button.clicked.connect(self.on_upload_clicked)
        self.upload_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
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
        """이메일 선택 처리"""
        if isinstance(item, EmailListItem):
            email_data = item.email_data
            # TODO: 해당 이메일의 태그 정보 조회
            tags_data = []  # 실제로는 데이터베이스에서 조회
            self.email_detail.show_email(email_data, tags_data)
            
            subject = email_data.get("subject", "제목 없음")
            self.status_changed.emit(f"이메일 선택: {subject}")
    
    def on_upload_clicked(self):
        """파일 업로드 버튼 클릭 처리"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "이메일 파일 선택",
            "",
            "EML Files (*.eml);;All Files (*)"
        )
        
        if file_paths:
            self.on_files_dropped(file_paths)
    
    def on_files_dropped(self, file_paths: List[str]):
        """파일 드롭 처리"""
        valid_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path.lower().endswith('.eml'):
                valid_files.append(file_path)
        
        if valid_files:
            self.progress_bar.show()
            self.progress_bar.setRange(0, len(valid_files))
            self.progress_bar.setValue(0)
            
            self.status_changed.emit(f"{len(valid_files)}개 파일 처리 시작...")
            self.email_processing_requested.emit(valid_files)
        else:
            QMessageBox.warning(self, "경고", "유효한 .eml 파일이 없습니다.")
    
    def update_progress(self, current: int, total: int):
        """진행 상황 업데이트"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
        if current >= total:
            self.progress_bar.hide()
            self.status_changed.emit("처리 완료")
    
    def show_processing_error(self, error_message: str):
        """처리 오류 표시"""
        self.progress_bar.hide()
        QMessageBox.critical(self, "오류", f"이메일 처리 중 오류가 발생했습니다:\n{error_message}")
        self.status_changed.emit("처리 실패") 