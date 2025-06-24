#!/usr/bin/env python3
"""
AI Smart Mailbox 메인 엔트리포인트
"""

import sys
import os
from pathlib import Path

# PyQt6 애플리케이션 임포트
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# GUI 모듈 임포트
from .gui import MainWindow

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
    
    # High DPI 스케일링 설정 (PyQt6에서는 자동으로 처리됨)
    # app.setAttribute 설정은 PyQt6에서 기본적으로 활성화됨
    
    try:
        # 메인 윈도우 생성 및 표시
        print("GUI 초기화 중...")
        window = MainWindow()
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