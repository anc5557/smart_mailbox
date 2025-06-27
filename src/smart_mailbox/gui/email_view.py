"""
AI Smart Mailbox 이메일 뷰
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QStackedWidget, QListWidget, QListWidgetItem,
    QTextEdit, QPushButton, QProgressBar, QFrame,
    QSplitter, QGroupBox, QScrollArea, QFileDialog, QMessageBox,
    QCheckBox, QToolButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QThread, QTimer, QSettings
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import re


class EmailDetailWidget(QWidget):
    """이메일 상세 보기 위젯"""
    
    reanalyze_requested = pyqtSignal(dict)  # 재분석 요청 시그널
    
    def __init__(self):
        super().__init__()
        self.current_email = None
        self.storage_manager = None  # 스토리지 매니저 추가
        self.setup_ui()
    
    def set_storage_manager(self, storage_manager):
        """스토리지 매니저를 설정합니다."""
        self.storage_manager = storage_manager
    
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
        
        # 답장 섹션 추가
        self.setup_reply_section(layout)
        
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
    
    def setup_reply_section(self, layout: QVBoxLayout):
        """답장 섹션 설정"""
        self.reply_group = QGroupBox("AI 자동 답장")
        reply_layout = QVBoxLayout(self.reply_group)
        
        # 답장 텍스트
        self.reply_text = QTextEdit()
        self.reply_text.setReadOnly(True)
        self.reply_text.setMaximumHeight(200)  # 높이 제한
        reply_layout.addWidget(self.reply_text)
        
        # 기본적으로 숨김
        self.reply_group.hide()
        
        layout.addWidget(self.reply_group)
    
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
        self.reanalyze_button.setToolTip("이 이메일을 다시 AI 분석합니다")
        actions_layout.addWidget(self.reanalyze_button)
        
        actions_layout.addStretch()
        layout.addWidget(actions_widget)
        
        # 버튼 이벤트 연결
        self.reanalyze_button.clicked.connect(self.on_reanalyze_clicked)
    
    def update_email(self, email_data: Dict[str, Any]):
        """이메일 데이터로 UI 업데이트"""
        self.current_email = email_data
        
        # 헤더 정보 업데이트 - 올바른 필드명 사용
        self.subject_label.setText(f"제목: {email_data.get('subject', 'N/A')}")
        
        # 발신자 정보 - sender와 sender_name 모두 확인
        sender_info = email_data.get('sender', 'N/A')
        sender_name = email_data.get('sender_name')
        if sender_name:
            sender_info = f"{sender_name} <{sender_info}>"
        self.sender_label.setText(f"발신자: {sender_info}")
        
        # 날짜 정보 - date_sent 필드 사용
        date_sent = email_data.get('date_sent', 'N/A')
        if isinstance(date_sent, datetime):
            formatted_date = date_sent.strftime('%Y-%m-%d %H:%M')
        else:
            formatted_date = str(date_sent)
        self.date_label.setText(f"날짜: {formatted_date}")
        
        # 본문 업데이트 - body_text 필드 사용
        body_text = email_data.get('body_text', '')
        if not body_text:
            body_html = email_data.get('body_html', '')
            if body_html:
                # HTML 태그 제거하여 텍스트만 추출
                body_text = re.sub(r'<[^>]+>', '', body_html)
                body_text = body_text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            else:
                body_text = '본문이 없습니다.'
        self.body_text.setPlainText(body_text)
        
        # 태그 정보 업데이트 - tags 필드에서 가져오기
        tags = email_data.get('tags', [])
        ai_processed = email_data.get('ai_processed', False)
        
        print(f"🏷️ [DEBUG] 이메일 태그 정보:")
        print(f"   - tags: {tags} (타입: {type(tags)})")
        print(f"   - ai_processed: {ai_processed}")
        print(f"   - 이메일 ID: {email_data.get('id', 'N/A')}")
        print(f"   - 제목: {email_data.get('subject', 'N/A')[:50]}...")
        
        if tags:
            # 태그가 리스트인지 확인
            if isinstance(tags, list):
                # 태그가 딕셔너리 형태인지 문자열인지 확인
                if tags and isinstance(tags[0], dict):
                    tags_text = ', '.join([f"🏷️ {tag.get('display_name', tag.get('name', ''))}" for tag in tags])
                else:
                    tags_text = ', '.join([f"🏷️ {tag}" for tag in tags])
            else:
                tags_text = f"🏷️ {tags}"
            
            self.tags_label.setText(tags_text)
            self.tags_group.show()
            print(f"✅ 태그 표시됨: {tags_text}")
        else:
            if ai_processed:
                self.tags_label.setText("태그 없음")
                print("✅ [DEBUG] AI 처리 완료 - 태그 없음으로 설정")
            else:
                self.tags_label.setText("분석 중...")
                print("⏳ [DEBUG] AI 미처리 - 분석 중으로 설정")
            self.tags_group.show()  # 태그 섹션은 항상 표시
        
        # 첨부파일 정보 업데이트
        has_attachments = email_data.get('has_attachments', False)
        attachment_count = email_data.get('attachment_count', 0)
        
        if has_attachments and attachment_count > 0:
            attachment_info = email_data.get('attachment_info', '')
            if attachment_info:
                self.attachments_label.setText(f"첨부파일 {attachment_count}개: {attachment_info}")
            else:
                self.attachments_label.setText(f"첨부파일 {attachment_count}개")
            self.attachments_group.show()
        else:
            self.attachments_label.setText("첨부파일이 없습니다.")
            self.attachments_group.hide()
        
        # 답장 정보 업데이트
        self._load_generated_replies(email_data)
        
        # 이메일 상세 위젯을 명시적으로 표시
        self.show()
        print(f"✅ [DEBUG] 이메일 상세 정보 표시 완료: {email_data.get('subject', 'N/A')[:30]}...")
    
    def _load_generated_replies(self, email_data: Dict[str, Any]):
        """이메일에 대한 생성된 답장을 로드합니다."""
        try:
            if not self.storage_manager:
                self.reply_group.hide()
                return
            
            email_id = email_data.get('id')
            if not email_id:
                self.reply_group.hide()
                return
            
            # 해당 이메일에 대한 답장 찾기
            replies = self.storage_manager.get_generated_replies_for_email(email_id)
            
            if replies:
                print(f"💬 [DEBUG] {len(replies)}개의 답장 발견됨")
                
                # 가장 최신 답장 표시
                latest_reply = replies[0]
                reply_content = latest_reply.get('body_text', '')
                reply_date = latest_reply.get('date_sent', '')
                
                # 답장 텍스트 설정
                if reply_content:
                    display_text = f"생성 일시: {reply_date}\n\n{reply_content}"
                    self.reply_text.setPlainText(display_text)
                    self.reply_group.show()
                    print(f"✅ [DEBUG] 답장 표시됨: {reply_content[:50]}...")
                else:
                    self.reply_group.hide()
            else:
                print(f"📭 [DEBUG] 답장 없음")
                self.reply_group.hide()
                
        except Exception as e:
            print(f"❌ 답장 로드 실패: {e}")
            self.reply_group.hide()
    
    def on_reanalyze_clicked(self):
        """재분석 버튼 클릭 시 호출"""
        if self.current_email:
            print(f"🔄 [DEBUG] 재분석 요청: {self.current_email.get('subject', 'N/A')[:50]}...")
            self.reanalyze_requested.emit(self.current_email)
        
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


class EmailTableWidget(QTableWidget):
    """드래그 앤 드롭 지원 이메일 테이블"""
    
    files_dropped = pyqtSignal(list)  # 드롭된 파일 목록
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        # 드래그 상태 추적
        self._drag_active = False
        
        # 테이블 설정
        self.setup_table()
    
    def setup_table(self):
        """테이블 초기 설정"""
        # 컬럼 설정
        headers = ["제목", "발신자", "날짜", "태그", "첨부"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 헤더 설정
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 제목 컬럼은 늘어남
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 발신자
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 날짜
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 태그
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 첨부
        
        # 세로 헤더 숨김
        self.verticalHeader().setVisible(False)
        
        # 흰색 바탕에 그리드 라인으로 구분
        self.setAlternatingRowColors(False)  # 대체 행 색상 비활성화
        self.setShowGrid(True)  # 그리드 라인 표시
        self.setGridStyle(Qt.PenStyle.SolidLine)  # 실선 그리드
        
        # 정렬 활성화
        self.setSortingEnabled(True)
        
        # 편집 비활성화 - 읽기 전용
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 행 선택 모드 설정
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # 행 단위 선택
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # 다중 선택 가능
        
        # 포커스 정책 설정 (클릭 시 전체 행 선택이 명확하게 보이도록)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """드래그 진입 이벤트"""
        if event.mimeData().hasUrls():
            self._drag_active = True
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """드래그 떠나기 이벤트"""
        self._drag_active = False
        super().dragLeaveEvent(event)
    
    def dragMoveEvent(self, event):
        """드래그 이동 이벤트"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """드롭 이벤트"""
        self._drag_active = False
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.endswith('.eml'):
                    file_paths.append(file_path)
            
            if file_paths:
                self.files_dropped.emit(file_paths)
            
            event.acceptProposedAction()
    
    def add_email_row(self, email_data: Dict[str, Any]):
        """이메일 데이터를 테이블 행으로 추가"""
        row = self.rowCount()
        self.insertRow(row)
        
        # 제목
        subject = email_data.get('subject', 'No Subject')
        subject_item = QTableWidgetItem(f"📧 {subject}")
        subject_item.setData(Qt.ItemDataRole.UserRole, email_data)  # 전체 이메일 데이터 저장
        self.setItem(row, 0, subject_item)
        
        # 발신자
        sender = email_data.get('sender', 'Unknown Sender')
        sender_name = email_data.get('sender_name')
        if sender_name:
            sender_display = f"{sender_name}"
        else:
            sender_display = sender
        sender_item = QTableWidgetItem(f"👤 {sender_display}")
        self.setItem(row, 1, sender_item)
        
        # 날짜
        date = email_data.get('date_sent', 'Unknown Date')
        try:
            if isinstance(date, datetime):
                formatted_date = date.strftime('%Y-%m-%d %H:%M')
            elif isinstance(date, str) and date != 'Unknown Date':
                if 'T' in date or '-' in date:
                    parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = parsed_date.strftime('%Y-%m-%d %H:%M')
                else:
                    formatted_date = str(date)
            else:
                formatted_date = str(date)
        except Exception:
            formatted_date = str(date)
        
        date_item = QTableWidgetItem(f"📅 {formatted_date}")
        self.setItem(row, 2, date_item)
        
        # 태그
        tags = email_data.get('tags', [])
        if tags:
            if isinstance(tags, list):
                if tags and isinstance(tags[0], dict):
                    tags_text = ', '.join([tag.get('display_name', tag.get('name', '')) for tag in tags])
                else:
                    tags_text = ', '.join([str(tag) for tag in tags])
            else:
                tags_text = str(tags)
            tags_display = f"🏷️ {tags_text}"
        else:
            ai_processed = email_data.get('ai_processed', False)
            tags_display = "태그 없음" if ai_processed else "분석 중..."
        
        tags_item = QTableWidgetItem(tags_display)
        self.setItem(row, 3, tags_item)
        
        # 첨부파일
        has_attachments = email_data.get('has_attachments', False)
        attachment_count = email_data.get('attachment_count', 0)
        if has_attachments and attachment_count > 0:
            attachment_display = f"📎 {attachment_count}개"
        else:
            attachment_display = ""
        
        attachment_item = QTableWidgetItem(attachment_display)
        self.setItem(row, 4, attachment_item)


class EmailView(QWidget):
    """메인 이메일 뷰"""
    
    status_changed = pyqtSignal(str)
    files_processing = pyqtSignal(list)  # 파일 처리 요청 시그널
    emails_deleted = pyqtSignal(list)  # 이메일 삭제 요청 시그널
    reanalyze_requested = pyqtSignal(dict)  # 이메일 재분석 요청 시그널
    reload_all_emails_requested = pyqtSignal()  # 전체 이메일 재로드 요청 시그널
    
    def __init__(self):
        super().__init__()
        self.current_emails = []
        self.file_manager = None
        self.storage_manager = None
        self.setup_ui()
    
    def set_storage_manager(self, storage_manager):
        """스토리지 매니저 설정"""
        self.storage_manager = storage_manager
        # EmailDetailWidget에도 스토리지 매니저 설정
        if hasattr(self, 'email_detail'):
            self.email_detail.set_storage_manager(storage_manager)
    
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 스플리터로 좌우 분할
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 왼쪽: 이메일 목록
        self.setup_email_list(splitter)
        
        # 오른쪽: 이메일 상세 정보
        self.email_detail = EmailDetailWidget()
        self.email_detail.reanalyze_requested.connect(self.on_reanalyze_requested)
        # 스토리지 매니저가 이미 설정되어 있으면 EmailDetailWidget에도 설정
        if self.storage_manager:
            self.email_detail.set_storage_manager(self.storage_manager)
        splitter.addWidget(self.email_detail)
        
        # 스플리터 비율 설정 (목록:상세 = 1:1)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)

    def setup_email_list(self, splitter: QSplitter):
        """이메일 목록 영역 설정"""
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setSpacing(0)
        
        # 헤더 섹션 (제목 + 툴바)
        self.setup_list_header(list_layout)
        
        # 이메일 테이블
        self.email_table = EmailTableWidget()
        self.email_table.cellClicked.connect(self.on_email_selected)
        self.email_table.files_dropped.connect(self.on_files_dropped)
        # 선택 변경 시 삭제 버튼 상태 업데이트
        self.email_table.itemSelectionChanged.connect(self.update_delete_button_state)
        list_layout.addWidget(self.email_table)
        
        # 진행바 섹션 (기본적으로 숨김)
        self.setup_progress_section(list_layout)
        
        splitter.addWidget(list_widget)

    def setup_list_header(self, layout: QVBoxLayout):
        """이메일 목록 헤더 섹션 설정 (제목 + 툴바)"""
        # 헤더 컨테이너
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 12, 12, 8)
        header_layout.setSpacing(8)
        
        # 제목
        self.list_title = QLabel("📧 전체 이메일")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.list_title.setFont(font)
        self.list_title.setObjectName("listTitle")
        header_layout.addWidget(self.list_title)
        
        # 툴바 (액션 버튼들)
        self.setup_toolbar(header_layout)
        
        # 헤더는 기본 테마 사용
        
        layout.addWidget(header_widget)

    def setup_toolbar(self, layout: QVBoxLayout):
        """툴바 설정 - 현대적인 버튼 스타일"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)
        
        # 파일 업로드 버튼 - 메인 액션
        self.upload_button = QPushButton()
        self.upload_button.setText("📁 이메일 파일 업로드")
        self.upload_button.setObjectName("uploadButton")
        self.upload_button.clicked.connect(self.on_upload_clicked)
        self.upload_button.setMinimumHeight(36)
        toolbar_layout.addWidget(self.upload_button)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #dee2e6;")
        toolbar_layout.addWidget(separator)
        
        # 선택 관련 버튼들
        self.select_all_button = QPushButton()
        self.select_all_button.setText("☑️ 전체 선택")
        self.select_all_button.setObjectName("selectButton")
        self.select_all_button.clicked.connect(self.toggle_select_all)
        self.select_all_button.setMinimumHeight(36)
        toolbar_layout.addWidget(self.select_all_button)
        
        # 삭제 버튼 - 위험한 액션
        self.delete_button = QPushButton()
        self.delete_button.setText("🗑️ 삭제")
        self.delete_button.setObjectName("deleteButton")
        self.delete_button.clicked.connect(self.on_delete_selected)
        self.delete_button.setEnabled(False)
        self.delete_button.setMinimumHeight(36)
        toolbar_layout.addWidget(self.delete_button)
        
        # 우측 여백
        toolbar_layout.addStretch()
        
        # 이메일 카운트 표시
        self.email_count_label = QLabel("0개 이메일")
        self.email_count_label.setObjectName("countLabel")
        toolbar_layout.addWidget(self.email_count_label)
        
        # 툴바는 기본 테마 사용
        
        layout.addWidget(toolbar_widget)
    
    def setup_progress_section(self, layout: QVBoxLayout):
        """진행바 섹션 설정"""
        # 진행바 컨테이너
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        progress_layout.setContentsMargins(10, 10, 10, 10)
        progress_layout.setSpacing(5)
        
        # 진행 상태 레이블
        self.progress_label = QLabel("이메일 처리 중...")
        progress_layout.addWidget(self.progress_label)
        
        # 진행바
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        # 상세 정보 레이블
        self.progress_detail = QLabel("")
        self.progress_detail.setWordWrap(True)
        progress_layout.addWidget(self.progress_detail)
        
        # 기본적으로 숨김
        self.progress_widget.hide()
        
        layout.addWidget(self.progress_widget)
    
    def update_delete_button_state(self):
        """삭제 버튼 상태 업데이트"""
        selected_rows = set()
        for item in self.email_table.selectedItems():
            selected_rows.add(item.row())
        count = len(selected_rows)
        
        if count == 0:
            self.delete_button.setEnabled(False)
            self.delete_button.setText("🗑️ 삭제")
        else:
            self.delete_button.setEnabled(True)
            self.delete_button.setText(f"🗑️ 삭제 ({count}개)")
    
    def toggle_select_all(self):
        """전체 선택/해제 토글"""
        if self.email_table.rowCount() == 0:
            return
            
        # 현재 선택된 행 수 확인
        selected_rows = set()
        for item in self.email_table.selectedItems():
            selected_rows.add(item.row())
        selected_count = len(selected_rows)
        total_count = self.email_table.rowCount()
        
        if selected_count == total_count:
            # 전체 선택된 경우 -> 전체 해제
            self.email_table.clearSelection()
            self.select_all_button.setText("☑️ 전체 선택")
        else:
            # 일부만 선택되거나 아무것도 선택되지 않은 경우 -> 전체 선택
            self.email_table.selectAll()
            self.select_all_button.setText("☐ 전체 해제")
    
    def on_delete_selected(self):
        """선택된 이메일들 삭제"""
        # 선택된 행들 수집
        selected_rows = set()
        for item in self.email_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        # 삭제할 이메일 목록 구성
        emails_to_delete = []
        for row in selected_rows:
            subject_item = self.email_table.item(row, 0)  # 제목 컬럼에서 이메일 데이터 가져오기
            if subject_item:
                email_data = subject_item.data(Qt.ItemDataRole.UserRole)
                if email_data:
                    emails_to_delete.append(email_data)
        
        if not emails_to_delete:
            return
        
        # 확인 다이얼로그
        count = len(emails_to_delete)
        reply = QMessageBox.question(
            self, 
            "이메일 삭제 확인",
            f"선택한 {count}개의 이메일을 삭제하시겠습니까?\n\n"
            "이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 삭제 요청 시그널 발송
            email_ids = [email['id'] for email in emails_to_delete]
            self.emails_deleted.emit(email_ids)
            
            # UI에서 즉시 제거 (낙관적 업데이트)
            # 높은 인덱스부터 제거 (인덱스 변경 방지)
            for row in sorted(selected_rows, reverse=True):
                self.email_table.removeRow(row)
            
            # 버튼 상태 업데이트
            self.update_delete_button_state()
            self.status_changed.emit(f"{count}개 이메일 삭제됨")
    
    def show_home_view(self):
        """홈 뷰 표시"""
        self.list_title.setText("📧 전체 이메일")
        # 이메일 목록 선택 해제 및 상세 뷰 클리어
        self.email_table.clearSelection()
        self.email_detail.clear()
        # 전체 이메일 재로드 요청 (필터링되지 않은 모든 이메일)
        self.reload_all_emails_requested.emit()
        self.status_changed.emit("전체 이메일 로딩 중...")
    
    def filter_by_tag(self, tag_name: str):
        """태그로 이메일 필터링"""
        try:
            # 이메일 목록 선택 해제 및 상세 뷰 클리어
            self.email_table.clearSelection()
            self.email_detail.clear()
            
            print(f"🔍 [DEBUG] 필터링 시작 - 태그: '{tag_name}'")
            
            # 스토리지에서 최신 이메일 목록 로드 (만약 storage_manager가 있다면)
            if self.storage_manager:
                fresh_emails = self.storage_manager.get_emails(limit=1000)
                print(f"🔍 [DEBUG] 스토리지에서 최신 이메일 로드: {len(fresh_emails)}개")
                emails_to_filter = fresh_emails
            else:
                print(f"🔍 [DEBUG] current_emails 사용: {len(self.current_emails)}개")
                emails_to_filter = self.current_emails
            
            # 해당 태그를 가진 이메일들만 필터링
            filtered_emails = []
            for i, email in enumerate(emails_to_filter):
                email_tags = email.get('tags', [])
                email_id = email.get('id', 'N/A')[:8]
                email_subject = email.get('subject', 'N/A')[:30]
                
                print(f"🔍 [DEBUG] 이메일 {i+1}: ID={email_id}, 제목='{email_subject}', 태그={email_tags} (타입: {type(email_tags)})")
                
                # 태그 매칭 검사
                is_matched = False
                
                if isinstance(email_tags, list):
                    # 태그 이름으로 검색 (딕셔너리 형태든 문자열 형태든 지원)
                    tag_names = []
                    for tag in email_tags:
                        if isinstance(tag, dict):
                            tag_names.append(tag.get('name', ''))
                        elif isinstance(tag, str):
                            tag_names.append(tag)
                        else:
                            tag_names.append(str(tag))
                    
                    # 공백 제거 후 비교
                    clean_tag_names = [name.strip() for name in tag_names if name and str(name).strip()]
                    print(f"🔍 [DEBUG]   → 추출된 태그 이름들: {clean_tag_names}")
                    
                    if tag_name in clean_tag_names:
                        is_matched = True
                        
                elif isinstance(email_tags, str):
                    # 단일 태그 문자열인 경우
                    clean_tag = email_tags.strip()
                    print(f"🔍 [DEBUG]   → 단일 태그 문자열: '{clean_tag}'")
                    if tag_name == clean_tag:
                        is_matched = True
                
                if is_matched:
                    filtered_emails.append(email)
                    print(f"✅ [DEBUG]   → 매칭됨! 필터링에 포함")
                else:
                    print(f"❌ [DEBUG]   → 매칭되지 않음")
                        
            print(f"🏷️ [DEBUG] '{tag_name}' 태그 필터링: {len(filtered_emails)}개 이메일 발견")
            self.list_title.setText(f"🏷️ {tag_name} 태그")
            self.update_email_list(filtered_emails)
            
            # 필터링 결과가 없을 때도 상세 뷰가 숨겨져 있는지 확인
            if not filtered_emails:
                self.email_detail.hide()
            
            self.status_changed.emit(f"'{tag_name}' 태그: {len(filtered_emails)}개 이메일")
        except Exception as e:
            print(f"❌ 태그 필터링 오류: {e}")
            import traceback
            traceback.print_exc()
            self.status_changed.emit(f"태그 필터링 실패: {e}")
    
    def update_email_list(self, emails_data: List[Dict[str, Any]]):
        """이메일 목록 업데이트"""
        self.current_emails = emails_data
        self.email_table.setRowCount(0)  # 테이블 클리어
        
        # 목록 업데이트 시 선택 해제 및 상세 뷰 클리어
        self.email_table.clearSelection()
        
        # 이메일 카운트 업데이트
        count = len(emails_data)
        self.email_count_label.setText(f"{count}개 이메일")
        
        if not emails_data:
            # 빈 상태일 때 상세 뷰 숨김
            self.email_detail.hide()
        else:
            for email_data in emails_data:
                self.email_table.add_email_row(email_data)
    
    def on_email_selected(self, row: int, column: int):
        """이메일 선택 이벤트"""
        subject_item = self.email_table.item(row, 0)  # 제목 컬럼에서 이메일 데이터 가져오기
        if subject_item:
            email_data = subject_item.data(Qt.ItemDataRole.UserRole)
            if email_data:
                self.email_detail.update_email(email_data)
                self.status_changed.emit(f"이메일 선택: {email_data.get('subject', 'N/A')}")
    
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
    
    def show_processing_progress(self, current: int, total: int, current_file: Optional[str] = None):
        """처리 진행률 표시"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
        # 진행률 계산
        percentage = int((current / total) * 100) if total > 0 else 0
        
        # 메인 레이블 업데이트
        self.progress_label.setText(f"📧 이메일 처리 중... ({current}/{total}) - {percentage}%")
        
        # 상세 정보 업데이트
        if current_file:
            import os
            filename = os.path.basename(current_file)
            self.progress_detail.setText(f"현재 파일: {filename}")
        else:
            if current == 0:
                self.progress_detail.setText("처리를 시작합니다...")
            elif current == total:
                self.progress_detail.setText("모든 파일 처리 완료!")
            else:
                self.progress_detail.setText(f"진행 중... {current}개 파일 완료됨")
        
        # 진행바 텍스트 설정
        self.progress_bar.setFormat(f"{current}/{total} ({percentage}%)")
        
        # 진행바 위젯 표시
        self.progress_widget.show()
        
        # 상태바 메시지
        self.status_changed.emit(f"이메일 처리 중... ({current}/{total}) - {percentage}%")
    
    def hide_processing_progress(self):
        """처리 진행률 숨김"""
        self.progress_widget.hide()
    
    def show_processing_error(self, error_message: str):
        """처리 오류 표시"""
        self.progress_bar.hide()
        QMessageBox.critical(self, "오류", f"이메일 처리 중 오류가 발생했습니다:\n{error_message}")
        self.status_changed.emit("처리 실패")
    
    def on_reanalyze_requested(self, email_data: Dict[str, Any]):
        """재분석 요청 처리"""
        print(f"📧 [DEBUG] EmailView에서 재분석 요청 수신: {email_data.get('subject', 'N/A')[:50]}...")
        self.reanalyze_requested.emit(email_data) 