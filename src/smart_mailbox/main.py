#!/usr/bin/env python3
"""
AI Smart Mailbox 메인 엔트리포인트
"""

import sys
import os
from pathlib import Path

# PyQt6 애플리케이션 임포트
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSettings

# GUI 모듈 임포트
from .gui import MainWindow

# 테마 적용을 위한 라이브러리
import qdarktheme

def apply_theme(theme: str):
    """설정에 따라 애플리케이션 테마를 적용합니다."""
    print(f"🎨 apply_theme 호출됨: {theme}")  # 디버깅용
    
    # qdarktheme는 "system" 대신 "auto"를 사용
    if theme == "system":
        theme = "auto"
        print(f"🔄 system → auto 변환")  # 디버깅용
    
    try:
        qdarktheme.setup_theme(theme=theme)
        print(f"✅ 테마 적용 성공: {theme}")
        
    except Exception as e:
        print(f"❌ 테마 적용 실패: {e}")


def main():
    """메인 애플리케이션 엔트리포인트"""
    print("🤖 AI Smart Mailbox 시작 중...")
    print(f"Python 버전: {sys.version}")
    print(f"작업 디렉토리: {os.getcwd()}")
    
    # PyQt6 애플리케이션 생성
    app = QApplication(sys.argv)
    app.setApplicationName("AI Smart Mailbox")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Smart Mailbox")
    app.setOrganizationDomain("smartmailbox.local")
    
    # 초기 테마 적용
    settings = QSettings()
    initial_theme = settings.value("general/theme", "auto", type=str)
    apply_theme(initial_theme)
    
    try:
        # 메인 윈도우 생성 및 표시
        print("GUI 초기화 중...")
        window = MainWindow()
        
        # 설정 변경 시 테마 다시 적용
        window.theme_changed.connect(apply_theme)
        
        window.show()
        
        print("✅ AI Smart Mailbox가 성공적으로 시작되었습니다!")
        print("애플리케이션이 실행 중입니다. 창을 닫으면 종료됩니다.")
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ 애플리케이션 시작 중 오류 발생: {e}")
        print("GUI 라이브러리가 제대로 설치되었는지 확인해주세요.")
        return 1


if __name__ == "__main__":
    main() 