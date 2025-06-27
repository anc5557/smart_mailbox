"""
AI Smart Mailbox 사이드바
"""

from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, 
    QTreeWidgetItem, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette


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
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_widget)
    
    def setup_home_section(self, layout: QVBoxLayout):
        """홈 섹션 설정"""
        self.home_button = QPushButton("📥 홈 (전체)")
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
        
        # 태그 선택 이벤트 연결
        self.tags_tree.itemClicked.connect(self.on_tag_clicked)
        
        layout.addWidget(self.tags_tree)
    
    def setup_actions_section(self, layout: QVBoxLayout):
        """액션 버튼 영역 설정"""
        # 새로고침 버튼
        self.refresh_button = QPushButton("🔄 새로고침")
        self.refresh_button.setToolTip("이메일 목록과 태그를 새로고침합니다")
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        layout.addWidget(self.refresh_button)
    
    def on_home_clicked(self):
        """홈 버튼 클릭 처리"""
        self.current_selected_tag = None
        
        # 모든 태그 선택 해제
        self.tags_tree.clearSelection()
        
        # 홈 버튼 선택 (스타일은 기본 테마 사용)
        
        self.home_selected.emit()
    
    def on_tag_clicked(self, item: QTreeWidgetItem, column: int):
        """태그 클릭 처리"""
        if item:
            tag_name = item.data(0, Qt.ItemDataRole.UserRole)
            if tag_name:
                # 동일한 태그를 다시 클릭한 경우 처리
                if self.current_selected_tag == tag_name:
                    print(f"🏷️ [DEBUG] 동일한 태그 재클릭: {tag_name}")
                else:
                    print(f"🏷️ [DEBUG] 태그 선택: {self.current_selected_tag} → {tag_name}")
                
                self.current_selected_tag = tag_name
                self.tag_selected.emit(tag_name)
    
    def on_refresh_clicked(self):
        """새로고침 버튼 클릭 처리"""
        self.refresh_requested.emit()
    
    def update_tags(self, tags_data: List[Dict[str, Any]]):
        """태그 목록 업데이트"""
        self.tags_tree.clear()
        
        if not tags_data:
            # 태그가 없을 때 표시
            no_tags_item = QTreeWidgetItem(["📝 태그 없음"])
            no_tags_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 비활성화
            self.tags_tree.addTopLevelItem(no_tags_item)
            return
        
        for tag_data in tags_data:
            tag_name = tag_data.get('name', '')
            display_name = tag_data.get('display_name', tag_name)
            count = tag_data.get('count', 0)
            color = tag_data.get('color', '#007ACC')
            
            # 태그 아이템 생성
            item_text = f"🏷️ {display_name} ({count})"
            item = QTreeWidgetItem([item_text])
            
            # 태그 이름 저장 (클릭 시 사용)
            item.setData(0, Qt.ItemDataRole.UserRole, tag_name)
            
            # 색상 설정 (간단하게)
            item.setForeground(0, QColor(color))
            
            self.tags_tree.addTopLevelItem(item)
    
    def select_tag(self, tag_name: str):
        """프로그래밍적으로 태그 선택"""
        for i in range(self.tags_tree.topLevelItemCount()):
            item = self.tags_tree.topLevelItem(i)
            stored_tag_name = item.data(0, Qt.ItemDataRole.UserRole)
            if stored_tag_name == tag_name:
                self.tags_tree.setCurrentItem(item)
                self.current_selected_tag = tag_name
                break
    
    def get_selected_tag(self) -> Optional[str]:
        """현재 선택된 태그 반환"""
        return self.current_selected_tag 
    
    def clear_selection(self):
        """모든 선택을 해제 (검색 모드일 때 사용)"""
        self.current_selected_tag = None
        self.tags_tree.clearSelection() 