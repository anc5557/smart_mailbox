"""
AI Smart Mailbox 설정 창
"""

from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QCheckBox, QSpinBox, QTextEdit, QComboBox,
    QFormLayout, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class OllamaSettingsTab(QWidget):
    """Ollama 설정 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 연결 설정 그룹
        connection_group = QGroupBox("연결 설정")
        connection_layout = QFormLayout(connection_group)
        
        self.server_url_edit = QLineEdit("http://localhost:11434")
        connection_layout.addRow("서버 URL:", self.server_url_edit)
        
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama2", "codellama", "mistral", "llama3"])
        connection_layout.addRow("사용할 모델:", self.model_combo)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setSuffix("초")
        connection_layout.addRow("타임아웃:", self.timeout_spin)
        
        # 연결 테스트 버튼
        test_layout = QHBoxLayout()
        test_button = QPushButton("연결 테스트")
        test_button.clicked.connect(self.test_connection)
        test_layout.addWidget(test_button)
        test_layout.addStretch()
        
        connection_layout.addRow(test_layout)
        layout.addWidget(connection_group)
        
        # AI 설정 그룹
        ai_group = QGroupBox("AI 설정")
        ai_layout = QFormLayout(ai_group)
        
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 100)
        self.temperature_spin.setValue(70)
        ai_layout.addRow("창의성 (Temperature):", self.temperature_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4096)
        self.max_tokens_spin.setValue(1024)
        ai_layout.addRow("최대 토큰 수:", self.max_tokens_spin)
        
        layout.addWidget(ai_group)
        
        # 여백 추가
        layout.addStretch()
        
    def test_connection(self):
        """연결 테스트"""
        # TODO: 실제 Ollama 연결 테스트 구현
        QMessageBox.information(self, "연결 테스트", "연결 테스트 기능은 구현 예정입니다.")
        
    def get_settings(self) -> dict:
        """설정 값 반환"""
        return {
            'server_url': self.server_url_edit.text(),
            'model': self.model_combo.currentText(),
            'timeout': self.timeout_spin.value(),
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value()
        }
        
    def set_settings(self, settings: dict):
        """설정 값 적용"""
        if 'server_url' in settings:
            self.server_url_edit.setText(settings['server_url'])
        if 'model' in settings:
            index = self.model_combo.findText(settings['model'])
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
        if 'timeout' in settings:
            self.timeout_spin.setValue(settings['timeout'])
        if 'temperature' in settings:
            self.temperature_spin.setValue(int(settings['temperature'] * 100))
        if 'max_tokens' in settings:
            self.max_tokens_spin.setValue(settings['max_tokens'])


class TagSettingsTab(QWidget):
    """태그 설정 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 기본 태그 설정
        default_group = QGroupBox("기본 태그 설정")
        default_layout = QVBoxLayout(default_group)
        
        self.important_check = QCheckBox("🔴 중요")
        self.important_check.setChecked(True)
        default_layout.addWidget(self.important_check)
        
        self.reply_check = QCheckBox("💬 회신필요")
        self.reply_check.setChecked(True)
        default_layout.addWidget(self.reply_check)
        
        self.spam_check = QCheckBox("🚫 스팸")
        self.spam_check.setChecked(True)
        default_layout.addWidget(self.spam_check)
        
        self.ad_check = QCheckBox("📢 광고")
        self.ad_check.setChecked(True)
        default_layout.addWidget(self.ad_check)
        
        layout.addWidget(default_group)
        
        # 커스텀 태그 관리
        custom_group = QGroupBox("커스텀 태그 관리")
        custom_layout = QVBoxLayout(custom_group)
        
        # 태그 추가 섹션
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("새 태그:"))
        
        self.new_tag_edit = QLineEdit()
        self.new_tag_edit.setPlaceholderText("태그 이름 입력")
        add_layout.addWidget(self.new_tag_edit)
        
        add_button = QPushButton("추가")
        add_button.clicked.connect(self.add_custom_tag)
        add_layout.addWidget(add_button)
        
        custom_layout.addLayout(add_layout)
        
        # 기존 커스텀 태그 목록
        self.custom_tags_text = QTextEdit()
        self.custom_tags_text.setMaximumHeight(100)
        self.custom_tags_text.setPlainText("(커스텀 태그가 없습니다)")
        custom_layout.addWidget(self.custom_tags_text)
        
        layout.addWidget(custom_group)
        
        # 여백 추가
        layout.addStretch()
        
    def add_custom_tag(self):
        """커스텀 태그 추가"""
        tag_name = self.new_tag_edit.text().strip()
        if tag_name:
            # TODO: 실제 커스텀 태그 저장 구현
            current_text = self.custom_tags_text.toPlainText()
            if current_text == "(커스텀 태그가 없습니다)":
                current_text = ""
            
            if current_text:
                new_text = f"{current_text}\n{tag_name}"
            else:
                new_text = tag_name
                
            self.custom_tags_text.setPlainText(new_text)
            self.new_tag_edit.clear()
            
    def get_settings(self) -> dict:
        """설정 값 반환"""
        return {
            'enabled_tags': {
                'important': self.important_check.isChecked(),
                'reply_needed': self.reply_check.isChecked(),
                'spam': self.spam_check.isChecked(),
                'advertisement': self.ad_check.isChecked()
            },
            'custom_tags': self.custom_tags_text.toPlainText().split('\n')
        }


class GeneralSettingsTab(QWidget):
    """일반 설정 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 애플리케이션 설정
        app_group = QGroupBox("애플리케이션 설정")
        app_layout = QFormLayout(app_group)
        
        self.auto_start_check = QCheckBox("시스템 시작 시 자동 실행")
        app_layout.addRow(self.auto_start_check)
        
        self.minimize_tray_check = QCheckBox("닫기 버튼 클릭 시 트레이로 최소화")
        app_layout.addRow(self.minimize_tray_check)
        
        self.auto_save_check = QCheckBox("자동 저장 활성화")
        self.auto_save_check.setChecked(True)
        app_layout.addRow(self.auto_save_check)
        
        layout.addWidget(app_group)
        
        # 데이터 설정
        data_group = QGroupBox("데이터 설정")
        data_layout = QFormLayout(data_group)
        
        self.backup_check = QCheckBox("자동 백업 활성화")
        data_layout.addRow(self.backup_check)
        
        self.backup_days_spin = QSpinBox()
        self.backup_days_spin.setRange(1, 30)
        self.backup_days_spin.setValue(7)
        self.backup_days_spin.setSuffix("일")
        data_layout.addRow("백업 주기:", self.backup_days_spin)
        
        layout.addWidget(data_group)
        
        # 여백 추가
        layout.addStretch()
        
    def get_settings(self) -> dict:
        """설정 값 반환"""
        return {
            'auto_start': self.auto_start_check.isChecked(),
            'minimize_to_tray': self.minimize_tray_check.isChecked(),
            'auto_save': self.auto_save_check.isChecked(),
            'auto_backup': self.backup_check.isChecked(),
            'backup_days': self.backup_days_spin.value()
        }


class SettingsDialog(QDialog):
    """설정 다이얼로그"""
    
    settings_changed = pyqtSignal(dict)  # 설정 변경 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("설정")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 탭 위젯
        tab_widget = QTabWidget()
        
        # 일반 설정 탭
        self.general_tab = GeneralSettingsTab()
        tab_widget.addTab(self.general_tab, "일반")
        
        # Ollama 설정 탭
        self.ollama_tab = OllamaSettingsTab()
        tab_widget.addTab(self.ollama_tab, "Ollama")
        
        # 태그 설정 탭
        self.tag_tab = TagSettingsTab()
        tab_widget.addTab(self.tag_tab, "태그")
        
        layout.addWidget(tab_widget)
        
        # 버튼 박스
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(button_box)
        
    def accept_settings(self):
        """설정 적용하고 창 닫기"""
        self.apply_settings()
        self.accept()
        
    def apply_settings(self):
        """설정 적용"""
        settings = {
            'general': self.general_tab.get_settings(),
            'ollama': self.ollama_tab.get_settings(),
            'tags': self.tag_tab.get_settings()
        }
        
        self.settings_changed.emit(settings)
        
    def load_settings(self, settings: dict):
        """설정 로드"""
        if 'general' in settings:
            # TODO: 일반 설정 로드 구현
            pass
        if 'ollama' in settings:
            self.ollama_tab.set_settings(settings['ollama'])
        if 'tags' in settings:
            # TODO: 태그 설정 로드 구현
            pass 