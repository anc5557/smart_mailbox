"""
AI Smart Mailbox 설정 창
"""

from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QCheckBox, QSpinBox, QTextEdit, QComboBox,
    QFormLayout, QDialogButtonBox, QMessageBox,
    QListWidget, QListWidgetItem, QColorDialog, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

from ..config.tags import TagConfig
from ..config.ai import AIConfig
from ..ai.ollama_client import OllamaClient, OllamaConfig


class OllamaSettingsTab(QWidget):
    """Ollama 설정 탭"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        connection_group = QGroupBox("연결 설정")
        connection_layout = QVBoxLayout(connection_group)
        
        # 서버 URL
        url_layout = QHBoxLayout()
        url_label = QLabel("서버 URL:")
        url_label.setMinimumWidth(120)
        url_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.server_url_edit = QLineEdit("http://localhost:11434")
        self.server_url_edit.setMinimumWidth(300)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.server_url_edit)
        url_layout.addStretch()
        connection_layout.addLayout(url_layout)
        
        # 모델 선택
        model_layout = QHBoxLayout()
        model_label = QLabel("사용할 모델:")
        model_label.setMinimumWidth(120)
        model_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.model_combo.setToolTip("연결 테스트 후 사용 가능한 모델 목록이 표시됩니다.")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        connection_layout.addLayout(model_layout)
        
        # 타임아웃
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("타임아웃:")
        timeout_label.setMinimumWidth(120)
        timeout_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(60)
        self.timeout_spin.setSuffix("초")
        self.timeout_spin.setMinimumWidth(100)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        connection_layout.addLayout(timeout_layout)
        
        # 연결 상태 및 테스트
        test_layout = QHBoxLayout()
        status_label = QLabel("연결 상태:")
        status_label.setMinimumWidth(120)
        status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.connection_status_label = QLabel("확인 필요")
        test_button = QPushButton("연결 테스트")
        test_button.clicked.connect(self.test_connection)
        test_button.setMaximumWidth(120)
        
        test_layout.addWidget(status_label)
        test_layout.addWidget(self.connection_status_label)
        test_layout.addStretch()
        test_layout.addWidget(test_button)
        
        connection_layout.addLayout(test_layout)
        layout.addWidget(connection_group)
        
        ai_group = QGroupBox("AI 설정")
        ai_layout = QVBoxLayout(ai_group)
        
        # 창의성 (Temperature)
        temp_layout = QHBoxLayout()
        temp_label = QLabel("창의성 (Temperature):")
        temp_label.setMinimumWidth(120)
        temp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 100)
        self.temperature_spin.setValue(70)
        self.temperature_spin.setMinimumWidth(100)
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_spin)
        temp_layout.addStretch()
        ai_layout.addLayout(temp_layout)
        
        # 최대 토큰 수
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("최대 토큰 수:")
        tokens_label.setMinimumWidth(120)
        tokens_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4096)
        self.max_tokens_spin.setValue(1024)
        self.max_tokens_spin.setMinimumWidth(100)
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.max_tokens_spin)
        tokens_layout.addStretch()
        ai_layout.addLayout(tokens_layout)
        
        # Thinking 비활성화
        thinking_layout = QHBoxLayout()
        thinking_label = QLabel("Thinking 비활성화:")
        thinking_label.setMinimumWidth(120)
        thinking_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.disable_thinking_checkbox = QCheckBox()
        self.disable_thinking_checkbox.setToolTip("AI가 응답하기 전에 'thinking' 과정을 표시하지 않도록 합니다.")
        self.disable_thinking_checkbox.setChecked(True)
        thinking_layout.addWidget(thinking_label)
        thinking_layout.addWidget(self.disable_thinking_checkbox)
        thinking_layout.addStretch()
        ai_layout.addLayout(thinking_layout)
        
        layout.addWidget(ai_group)
        layout.addStretch()
        
    def test_connection(self):
        """Ollama 서버 연결 테스트 및 모델 목록 가져오기"""
        self.connection_status_label.setText("확인 중...")
        self.repaint()

        config = OllamaConfig(
            base_url=self.server_url_edit.text(),
            timeout=self.timeout_spin.value()
        )
        client = OllamaClient(config)
        
        try:
            is_connected, models = client.check_connection()
            
            if is_connected:
                self.connection_status_label.setText("<font color='green'>연결됨</font>")
                
                current_model = self.model_combo.currentText()
                self.model_combo.clear()
                if models:
                    self.model_combo.addItems(models)
                    if current_model in models:
                        self.model_combo.setCurrentText(current_model)
                    QMessageBox.information(self, "연결 성공", f"Ollama 서버에 성공적으로 연결되었습니다.\n사용 가능한 모델 {len(models)}개를 불러왔습니다.")
                else:
                    QMessageBox.warning(self, "연결 성공", "Ollama 서버에 연결되었지만, 사용 가능한 모델이 없습니다.")
            else:
                self.connection_status_label.setText("<font color='red'>연결 실패</font>")
                self.model_combo.clear()
                QMessageBox.critical(self, "연결 실패", "Ollama 서버에 연결할 수 없습니다.\nURL과 서버 상태를 확인해주세요.")
        
        finally:
            client.close()
    
    def auto_test_connection(self):
        """설정 로드 시 자동으로 연결 테스트 (백그라운드에서 조용히 수행)"""
        config = OllamaConfig(
            base_url=self.server_url_edit.text(),
            timeout=self.timeout_spin.value()
        )
        client = OllamaClient(config)
        
        try:
            is_connected, models = client.check_connection()
            
            if is_connected:
                self.connection_status_label.setText("<font color='green'>연결됨</font>")
                
                current_model = self.model_combo.currentText()
                self.model_combo.clear()
                if models:
                    self.model_combo.addItems(models)
                    if current_model in models:
                        self.model_combo.setCurrentText(current_model)
            else:
                self.connection_status_label.setText("<font color='red'>연결 실패</font>")
                self.model_combo.clear()
        
        except Exception:
            # 자동 테스트에서는 오류를 조용히 처리
            self.connection_status_label.setText("<font color='red'>연결 실패</font>")
            self.model_combo.clear()
        
        finally:
            client.close()
        
    def get_settings(self) -> dict:
        return {
            'server_url': self.server_url_edit.text(),
            'model': self.model_combo.currentText(),
            'timeout': self.timeout_spin.value(),
            'temperature': self.temperature_spin.value() / 100.0,
            'max_tokens': self.max_tokens_spin.value(),
            'disable_thinking': self.disable_thinking_checkbox.isChecked()
        }
        
    def set_settings(self, settings: dict):
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
        if 'disable_thinking' in settings:
            self.disable_thinking_checkbox.setChecked(settings['disable_thinking'])
        
        # 설정 로드 후 자동으로 연결 테스트 수행
        self.auto_test_connection()


class TagSettingsTab(QWidget):
    """태그 설정 탭"""
    
    def __init__(self, tag_config: TagConfig, parent=None):
        super().__init__(parent)
        self.tag_config = tag_config
        self.setup_ui()
        self.load_tags()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Tag list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("태그 목록"))
        self.tag_list_widget = QListWidget()
        self.tag_list_widget.currentItemChanged.connect(self.display_tag_details)
        left_layout.addWidget(self.tag_list_widget)

        # Right side: Tag details
        right_widget = QWidget()
        self.right_layout = QVBoxLayout(right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        self.tag_details_group = QGroupBox("태그 상세 정보")
        self.tag_details_group.setVisible(False)
        details_layout = QFormLayout(self.tag_details_group)

        self.tag_name_edit = QLineEdit()
        self.tag_name_edit.setReadOnly(True)
        details_layout.addRow("이름:", self.tag_name_edit)

        color_layout = QHBoxLayout()
        self.color_button = QPushButton()
        self.color_button.setFixedWidth(100)
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        details_layout.addRow("색상:", color_layout)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setFixedHeight(100)
        details_layout.addRow("AI 프롬프트:", self.prompt_edit)
        
        self.right_layout.addWidget(self.tag_details_group)
        self.right_layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        self.add_tag_button = QPushButton("새 태그 추가")
        self.add_tag_button.clicked.connect(self.add_new_tag)
        self.delete_tag_button = QPushButton("태그 삭제")
        self.delete_tag_button.clicked.connect(self.delete_selected_tag)
        self.delete_tag_button.setEnabled(False)
        
        button_layout.addWidget(self.add_tag_button)
        button_layout.addWidget(self.delete_tag_button)
        left_layout.addLayout(button_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 300])
        main_layout.addWidget(splitter)

    def load_tags(self):
        # Save current selection
        current_row = self.tag_list_widget.currentRow()
        
        self.tag_list_widget.clear()
        tags = self.tag_config.get_all_tags()
        for name, details in tags.items():
            item = QListWidgetItem(name)
            item.setForeground(QColor(details.get('color', '#000000')))
            self.tag_list_widget.addItem(item)
            
        # Restore selection
        if current_row != -1 and current_row < self.tag_list_widget.count():
            self.tag_list_widget.setCurrentRow(current_row)

    def display_tag_details(self, current: QListWidgetItem, previous: QListWidgetItem):
        if not current:
            self.tag_details_group.setVisible(False)
            return

        self.tag_details_group.setVisible(True)
        tag_name = current.text()
        tag_details = self.tag_config.get_all_tags()[tag_name]
        is_custom = tag_details.get("is_custom", False)

        self.tag_name_edit.setText(tag_name)
        
        color = QColor(tag_details.get('color', '#FFFFFF'))
        self.color_button.setStyleSheet(f"background-color: {color.name()};")
        
        self.prompt_edit.setText(tag_details.get('prompt', ''))
        
        # 기본 태그는 수정 불가
        self.color_button.setEnabled(is_custom)
        self.prompt_edit.setReadOnly(not is_custom)
        self.delete_tag_button.setEnabled(is_custom)

    def choose_color(self):
        style = self.color_button.styleSheet()
        color_name = '#FFFFFF'
        if 'background-color' in style:
            # "background-color: #RRGGBB;" -> "#RRGGBB"
            color_name = style.split(':')[1].strip().split(';')[0]
        
        current_color = QColor(color_name)
        color = QColorDialog.getColor(current_color, self)
        if color.isValid():
            self.color_button.setStyleSheet(f"background-color: {color.name()};")

    def add_new_tag(self):
        # 간단한 다이얼로그로 새 태그 정보 입력 받기
        dialog = QDialog(self)
        dialog.setWindowTitle("새 커스텀 태그 추가")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        layout.addRow("태그 이름:", name_edit)
        
        prompt_edit = QTextEdit("이 이메일이 [태그 설명]에 해당하는지 판단합니다.")
        layout.addRow("AI 프롬프트:", prompt_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec():
            name = name_edit.text().strip()
            prompt = prompt_edit.toPlainText().strip()
            if name and prompt:
                if self.tag_config.add_custom_tag(name, "#C0C0C0", prompt):
                    self.load_tags()
                    QMessageBox.information(self, "성공", f"'{name}' 태그를 추가했습니다.")
                else:
                    QMessageBox.warning(self, "오류", f"'{name}' 태그는 이미 존재합니다.")
            else:
                QMessageBox.warning(self, "오류", "태그 이름과 프롬프트를 모두 입력해야 합니다.")

    def delete_selected_tag(self):
        current_item = self.tag_list_widget.currentItem()
        if not current_item:
            return

        tag_name = current_item.text()
        reply = QMessageBox.question(self, "태그 삭제", f"'{tag_name}' 태그를 정말 삭제하시겠습니까?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.tag_config.delete_custom_tag(tag_name):
                self.load_tags()
                self.tag_details_group.setVisible(False)
                QMessageBox.information(self, "성공", f"'{tag_name}' 태그를 삭제했습니다.")
            else:
                QMessageBox.warning(self, "오류", "기본 태그는 삭제할 수 없습니다.")

    def apply_changes(self):
        """태그 변경사항 저장"""
        current_item = self.tag_list_widget.currentItem()
        if not current_item:
            # No item selected, nothing to apply.
            return

        tag_name = current_item.text()
        tag_details = self.tag_config.get_all_tags().get(tag_name)

        if tag_details and tag_details.get("is_custom", False):
            # Get color from button stylesheet
            style = self.color_button.styleSheet()
            new_color = tag_details.get('color') # default to old color
            if 'background-color' in style:
                color_name = style.split(':')[1].strip().split(';')[0]
                new_color = QColor(color_name).name()

            new_prompt = self.prompt_edit.toPlainText()
            
            self.tag_config.update_custom_tag(tag_name, new_color, new_prompt)
        
        # Reload all tags to reflect changes
        self.load_tags()

    def get_settings(self) -> dict:
        """설정 값 반환"""
        # 태그 설정은 TagConfig에서 직접 관리되므로 빈 딕셔너리 반환
        return {}


class GeneralSettingsTab(QWidget):
    """일반 설정 탭"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        app_group = QGroupBox("애플리케이션 설정")
        app_layout = QFormLayout(app_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Auto", "Light", "Dark"])
        self.theme_combo.setToolTip("애플리케이션의 테마를 설정합니다. Auto는 시스템 테마에 따라 자동 전환됩니다.")
        app_layout.addRow("테마:", self.theme_combo)

        self.auto_start_check = QCheckBox("시스템 시작 시 자동 실행")
        app_layout.addRow(self.auto_start_check)
        
        self.minimize_tray_check = QCheckBox("닫기 버튼 클릭 시 트레이로 최소화")
        app_layout.addRow(self.minimize_tray_check)
        
        self.auto_save_check = QCheckBox("자동 저장 활성화")
        self.auto_save_check.setChecked(True)
        app_layout.addRow(self.auto_save_check)
        
        layout.addWidget(app_group)
        
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
        layout.addStretch()
        
    def get_settings(self) -> dict:
        return {
            'theme': self.theme_combo.currentText().lower(),
            'auto_start': self.auto_start_check.isChecked(),
            'minimize_to_tray': self.minimize_tray_check.isChecked(),
            'auto_save': self.auto_save_check.isChecked(),
            'auto_backup': self.backup_check.isChecked(),
            'backup_days': self.backup_days_spin.value()
        }

    def set_settings(self, settings: dict):
        theme = settings.get('theme', 'auto')
        # 기존 'system'은 'auto'로 변환
        if theme == 'system':
            theme = 'auto'
        index = self.theme_combo.findText(theme.capitalize(), Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.auto_start_check.setChecked(settings.get('auto_start', False))
        self.minimize_tray_check.setChecked(settings.get('minimize_to_tray', False))
        self.auto_save_check.setChecked(settings.get('auto_save', True))
        self.backup_check.setChecked(settings.get('auto_backup', False))
        self.backup_days_spin.setValue(settings.get('backup_days', 7))


class SettingsDialog(QDialog):
    """설정 다이얼로그"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, tag_config: TagConfig, ai_config: AIConfig, parent=None):
        super().__init__(parent)
        self.tag_config = tag_config
        self.ai_config = ai_config
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("설정")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        tab_widget = QTabWidget()
        
        self.general_tab = GeneralSettingsTab()
        tab_widget.addTab(self.general_tab, "일반")
        
        self.ollama_tab = OllamaSettingsTab()
        tab_widget.addTab(self.ollama_tab, "Ollama")
        
        self.tag_tab = TagSettingsTab(self.tag_config)
        tab_widget.addTab(self.tag_tab, "태그")
        
        layout.addWidget(tab_widget)
        
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
        self.apply_settings()
        self.accept()
        
    def apply_settings(self):
        self.tag_tab.apply_changes()
        
        # Ollama/AI 설정 저장
        ollama_settings = self.ollama_tab.get_settings()
        ai_config_settings = {
            'model': ollama_settings.get('model', ''),
            'temperature': ollama_settings.get('temperature', 0.7),
            'max_tokens': ollama_settings.get('max_tokens', 1024),
            'disable_thinking': ollama_settings.get('disable_thinking', True),
            'server_url': ollama_settings.get('server_url', 'http://localhost:11434'),
            'timeout': ollama_settings.get('timeout', 60)
        }
        self.ai_config.update_settings(ai_config_settings)
        
        settings = {
            'general': self.general_tab.get_settings(),
            'ollama': ollama_settings,
        }
        
        self.settings_changed.emit(settings)
        QMessageBox.information(self, "설정 저장", "설정이 성공적으로 적용되었습니다.")

    def load_settings(self, settings: dict):
        if 'general' in settings:
            self.general_tab.set_settings(settings['general'])
        
        # AI 설정 파일에서 직접 로드
        ai_settings = {
            'model': self.ai_config.get_model(),
            'temperature': self.ai_config.get_setting('temperature', 0.7),
            'max_tokens': self.ai_config.get_setting('max_tokens', 1024),
            'disable_thinking': self.ai_config.get_setting('disable_thinking', True),
            'server_url': self.ai_config.get_setting('server_url', 'http://localhost:11434'),
            'timeout': self.ai_config.get_setting('timeout', 60)
        }
        
        # Ollama 설정이 있으면 일부 설정을 덮어쓰기
        if 'ollama' in settings:
            ai_settings.update(settings['ollama'])
        
        self.ollama_tab.set_settings(ai_settings)
        
        # Tag tab is loaded automatically from TagConfig
        self.tag_tab.load_tags() 