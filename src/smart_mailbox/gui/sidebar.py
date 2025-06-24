"""
AI Smart Mailbox 사이드바
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon


class Sidebar(QWidget):
    """좌측 사이드바 위젯"""
    
    # 시그널 정의
    tag_selected = pyqtSignal(str)  # 태그가 선택되었을 때
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_default_tags()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 제목
        title_label = QLabel("태그")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # 태그 목록
        self.tag_list = QListWidget()
        self.tag_list.setAlternatingRowColors(True)
        self.tag_list.itemClicked.connect(self.on_tag_clicked)
        layout.addWidget(self.tag_list)
        
        # 커스텀 태그 섹션
        custom_title_label = QLabel("커스텀 태그")
        custom_title_label.setFont(title_font)
        layout.addWidget(custom_title_label)
        
        # 커스텀 태그 버튼
        custom_buttons_layout = QHBoxLayout()
        
        add_tag_button = QPushButton("+ 추가")
        add_tag_button.clicked.connect(self.add_custom_tag)
        custom_buttons_layout.addWidget(add_tag_button)
        
        manage_tags_button = QPushButton("관리")
        manage_tags_button.clicked.connect(self.manage_tags)
        custom_buttons_layout.addWidget(manage_tags_button)
        
        layout.addLayout(custom_buttons_layout)
        
        # 커스텀 태그 목록
        self.custom_tag_list = QListWidget()
        self.custom_tag_list.setAlternatingRowColors(True)
        self.custom_tag_list.itemClicked.connect(self.on_tag_clicked)
        layout.addWidget(self.custom_tag_list)
        
        # 여백 추가
        layout.addStretch()
        
    def load_default_tags(self):
        """기본 태그 로드"""
        default_tags = [
            ("🏠 홈", "home"),
            ("🔴 중요", "important"),
            ("💬 회신필요", "reply_needed"),
            ("🚫 스팸", "spam"),
            ("📢 광고", "advertisement")
        ]
        
        for display_name, tag_name in default_tags:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, tag_name)
            self.tag_list.addItem(item)
            
        # 기본으로 홈 선택
        self.tag_list.setCurrentRow(0)
        
    def on_tag_clicked(self, item: QListWidgetItem):
        """태그 클릭 이벤트 처리"""
        tag_name = item.data(Qt.ItemDataRole.UserRole)
        if tag_name:
            self.tag_selected.emit(tag_name)
            
            # 다른 리스트의 선택 해제
            if self.sender() == self.tag_list:
                self.custom_tag_list.clearSelection()
            else:
                self.tag_list.clearSelection()
                
    def add_custom_tag(self):
        """커스텀 태그 추가"""
        # TODO: 커스텀 태그 추가 다이얼로그 구현
        print("커스텀 태그 추가 기능 구현 예정")
        
    def manage_tags(self):
        """태그 관리"""
        # TODO: 태그 관리 다이얼로그 구현
        print("태그 관리 기능 구현 예정")
        
    def add_custom_tag_item(self, display_name: str, tag_name: str):
        """커스텀 태그 아이템 추가"""
        item = QListWidgetItem(display_name)
        item.setData(Qt.ItemDataRole.UserRole, tag_name)
        self.custom_tag_list.addItem(item)
        
    def get_selected_tag(self) -> str:
        """현재 선택된 태그 반환"""
        # 기본 태그에서 선택된 항목 확인
        current_item = self.tag_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
            
        # 커스텀 태그에서 선택된 항목 확인
        current_item = self.custom_tag_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
            
        return "home"  # 기본값 