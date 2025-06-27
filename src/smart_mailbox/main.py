#!/usr/bin/env python3
"""
AI Smart Mailbox 메인 엔트리포인트
"""

import sys
import os

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import qdarktheme
from smart_mailbox.gui.main_window import MainWindow
from smart_mailbox.config.logger import logger

def apply_theme(app: QApplication, theme: str = "auto") -> None:
    """
    애플리케이션 테마 적용
    
    Args:
        app: Qt 애플리케이션
        theme: 테마 이름 ("light", "dark", "auto")
    """
    logger.debug(f"apply_theme 호출됨: {theme}")
    
    try:
        # 시스템 호환성을 위한 매핑
        if theme == "system":
            theme = "auto"
        
        # qdarktheme 적용
        qdarktheme.setup_theme(theme)
        logger.info(f"테마 적용 성공: {theme}")
    except Exception as e:
        logger.error(f"테마 적용 실패: {e}")
        # 기본 테마로 폴백
        try:
            app.setStyle("Fusion")
            logger.info("기본 Fusion 스타일로 폴백")
        except Exception as fallback_error:
            logger.error(f"폴백 테마 적용도 실패: {fallback_error}")


def main():
    """메인 함수"""
    logger.info("AI Smart Mailbox 시작 중...")
    logger.info(f"Python 버전: {sys.version}")
    logger.info(f"작업 디렉토리: {os.getcwd()}")
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI Smart Mailbox")
    app.setOrganizationName("SmartMailbox")
    
    try:
        # 메인 윈도우 생성
        logger.info("GUI 초기화 중...")
        window = MainWindow()
        
        # 테마 변경 시그널 연결
        window.theme_changed.connect(lambda theme: apply_theme(app, theme))
        
        # 초기 테마 적용 (설정에서 읽기)
        initial_theme = window.settings.value("general/theme", "auto", type=str)
        apply_theme(app, initial_theme)
        
        window.show()
        
        logger.info("AI Smart Mailbox가 성공적으로 시작되었습니다!")
        logger.info("애플리케이션이 실행 중입니다. 창을 닫으면 종료됩니다.")
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 중 오류 발생: {e}")
        logger.error("GUI 라이브러리가 제대로 설치되었는지 확인해주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main() 