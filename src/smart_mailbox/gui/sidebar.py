"""
AI Smart Mailbox 사이드바
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, 
    QTreeWidgetItem, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette


class TagItem(QTreeWidgetItem):
    """태그 아이템"""
    
    def __init__(self, tag_data: Dict[str, Any]):
        super().__init__()
        self.tag_data = tag_data
        self.setup_item()
    
    def setup_item(self):
        """아이템 설정"""
        # 태그 표시 이름과 개수
        display_text = self.tag_data.get("display_name", self.tag_data.get("name", ""))
        count = self.tag_data.get("count", 0)
        
        self.setText(0, f"{display_text} ({count})")
        
        # 시스템 태그와 커스텀 태그 구분
        if self.tag_data.get("is_system", False):
            font = QFont()
            font.setBold(True)
            self.setFont(0, font)
        
        # 태그 색상 적용
        color = self.tag_data.get("color", "#007ACC")
        self.setBackground(0, QColor(color + "20"))  # 투명도 추가
        
        # 데이터 저장
        self.setData(0, Qt.ItemDataRole.UserRole, self.tag_data)


class Sidebar(QWidget):
    """메인 사이드바"""
    
    # 시그널 정의
    tag_selected = pyqtSignal(str)  # 태그 이름
    home_selected = pyqtSignal()
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_selected_tag = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 앱 로고/제목
        self.setup_header(layout)
        
        # 홈 버튼
        self.setup_home_section(layout)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # 태그 목록
        self.setup_tags_section(layout)
        
        # 하단 액션 버튼들
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.setup_actions_section(layout)
    
    def setup_header(self, layout: QVBoxLayout):
        """헤더 영역 설정"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 앱 이름
        app_title = QLabel("🤖 Smart Mailbox")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        app_title.setFont(font)
        header_layout.addWidget(app_title)
        
        # 부제목
        subtitle = QLabel("AI 이메일 분석기")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 10px;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_widget)
    
    def setup_home_section(self, layout: QVBoxLayout):
        """홈 섹션 설정"""
        self.home_button = QPushButton("📥 홈 (전체)")
        self.home_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                background-color: transparent;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        self.home_button.clicked.connect(self.on_home_clicked)
        layout.addWidget(self.home_button)
    
    def setup_tags_section(self, layout: QVBoxLayout):
        """태그 섹션 설정"""
        # 태그 제목
        tags_label = QLabel("태그")
        font = QFont()
        font.setBold(True)
        tags_label.setFont(font)
        layout.addWidget(tags_label)
        
        # 태그 트리
        self.tags_tree = QTreeWidget()
        self.tags_tree.setHeaderHidden(True)
        self.tags_tree.setRootIsDecorated(False)
        self.tags_tree.setIndentation(10)
        self.tags_tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: transparent;
            }
            QTreeWidget::item {
                padding: 8px;
                border-radius: 5px;
                margin: 1px 0px;
            }
            QTreeWidget::item:hover {
                background-color: #e3f2fd;
            }
            QTreeWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
        """)
        
        # 태그 선택 이벤트 연결
        self.tags_tree.itemClicked.connect(self.on_tag_clicked)
        
        layout.addWidget(self.tags_tree)
    
    def setup_actions_section(self, layout: QVBoxLayout):
        """액션 버튼 섹션 설정"""
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(5)
        
        # 새로고침 버튼
        self.refresh_button = QPushButton("🔄 새로고침")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #ccc;
                background-color: #f5f5f5;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_requested.emit)
        actions_layout.addWidget(self.refresh_button)
        
        layout.addWidget(actions_widget)
    
    def update_tags(self, tags_data: List[Dict[str, Any]]):
        """태그 목록 업데이트"""
        self.tags_tree.clear()
        
        # 시스템 태그와 커스텀 태그 분리
        system_tags = []
        custom_tags = []
        
        for tag_data in tags_data:
            if tag_data.get("is_system", False):
                system_tags.append(tag_data)
            else:
                custom_tags.append(tag_data)
        
        # 시스템 태그 추가
        if system_tags:
            for tag_data in system_tags:
                tag_item = TagItem(tag_data)
                self.tags_tree.addTopLevelItem(tag_item)
        
        # 커스텀 태그가 있으면 구분선과 함께 추가
        if custom_tags:
            # 구분선 역할의 아이템
            separator_item = QTreeWidgetItem()
            separator_item.setText(0, "—— 커스텀 태그 ——")
            separator_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 선택 불가
            separator_item.setForeground(0, QColor("#888"))
            self.tags_tree.addTopLevelItem(separator_item)
            
            for tag_data in custom_tags:
                tag_item = TagItem(tag_data)
                self.tags_tree.addTopLevelItem(tag_item)
    
    def on_home_clicked(self):
        """홈 버튼 클릭 처리"""
        # 선택 상태 초기화
        self.tags_tree.clearSelection()
        self.current_selected_tag = None
        
        # 홈 버튼 스타일 변경
        self.home_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                background-color: #2196f3;
                color: white;
                border-radius: 5px;
            }
        """)
        
        # 시그널 발생
        self.home_selected.emit()
    
    def on_tag_clicked(self, item: QTreeWidgetItem, column: int):
        """태그 클릭 처리"""
        if not isinstance(item, TagItem):
            return
        
        # 홈 버튼 스타일 초기화
        self.home_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                background-color: transparent;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        
        # 선택된 태그 저장
        tag_data = item.tag_data
        tag_name = tag_data.get("name", "")
        self.current_selected_tag = tag_name
        
        # 시그널 발생
        self.tag_selected.emit(tag_name)
    
    def set_tag_count(self, tag_name: str, count: int):
        """특정 태그의 개수 업데이트"""
        for i in range(self.tags_tree.topLevelItemCount()):
            item = self.tags_tree.topLevelItem(i)
            if isinstance(item, TagItem):
                if item.tag_data.get("name") == tag_name:
                    item.tag_data["count"] = count
                    display_text = item.tag_data.get("display_name", tag_name)
                    item.setText(0, f"{display_text} ({count})")
                    break
    
    def get_current_selection(self) -> Optional[str]:
        """현재 선택된 태그 이름 반환"""
        return self.current_selected_tag
    
    def select_tag(self, tag_name: str):
        """프로그래밍 방식으로 태그 선택"""
        for i in range(self.tags_tree.topLevelItemCount()):
            item = self.tags_tree.topLevelItem(i)
            if isinstance(item, TagItem):
                if item.tag_data.get("name") == tag_name:
                    self.tags_tree.setCurrentItem(item)
                    self.on_tag_clicked(item, 0)
                    break
    
    def clear_selection(self):
        """선택 상태 초기화"""
        self.tags_tree.clearSelection()
        self.current_selected_tag = None
        
        # 홈 버튼 활성화
        self.on_home_clicked() 