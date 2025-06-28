#!/usr/bin/env python3
"""
Smart Mailbox 빌드 설정
"""

import os
import sys
from pathlib import Path

# 프로젝트 정보
APP_NAME = "Smart Mailbox"
APP_VERSION = "0.2.0"
APP_AUTHOR = "SmartMailbox Team"
APP_DESCRIPTION = "AI Smart Mailbox - 이메일 자동 태깅 및 답장 생성 도구"

# 경로 설정
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"
MAIN_SCRIPT = SRC_DIR / "smart_mailbox" / "main.py"
ASSETS_DIR = PROJECT_ROOT / "assets"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

# PyInstaller 공통 옵션
PYINSTALLER_OPTIONS = [
    "--name", APP_NAME,
    "--windowed",
    "--noconfirm",
    "--clean",
    f"--distpath={DIST_DIR}",
    f"--workpath={BUILD_DIR}",
    "--add-data", f"{SRC_DIR}{os.pathsep}.",
]

# Windows 전용 옵션
WINDOWS_OPTIONS = [
    "--onefile",
    "--version-file", "version_info.txt",
]

# macOS 전용 옵션  
MACOS_OPTIONS = [
    "--osx-bundle-identifier", "com.smartmailbox.app",
    # universal2는 문제가 있을 수 있으므로 제거
]

# 아이콘 추가 함수
def get_icon_options():
    """플랫폼에 맞는 아이콘 옵션 반환"""
    import sys
    
    if sys.platform == "win32":
        icon_path = ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            return ["--icon", str(icon_path)]
    elif sys.platform == "darwin":
        icon_path = ASSETS_DIR / "icon.icns"
        if icon_path.exists():
            return ["--icon", str(icon_path)]
    
    return []

# 숨겨진 임포트 (PyInstaller가 자동으로 감지하지 못하는 모듈들)
HIDDEN_IMPORTS = [
    "PyQt6.QtCore",
    "PyQt6.QtWidgets", 
    "PyQt6.QtGui",
    "qdarktheme",
    "langchain",
    "langchain_community",
    "ollama",
    "email.mime",
    "email.parser",
    "email.utils",
    "chardet",
    "cryptography",
    "pydantic",
]

def get_pyinstaller_command(platform="auto"):
    """플랫폼에 맞는 PyInstaller 명령어 생성"""
    if platform == "auto":
        platform = "windows" if sys.platform == "win32" else "macos"
    
    cmd = ["pyinstaller"] + PYINSTALLER_OPTIONS.copy()
    
    # 숨겨진 임포트 추가
    for module in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module])
    
    # 아이콘 옵션 추가
    cmd.extend(get_icon_options())
    
    # 플랫폼별 옵션 추가
    if platform == "windows":
        cmd.extend(WINDOWS_OPTIONS)
    elif platform == "macos":
        cmd.extend(MACOS_OPTIONS)
    
    # 메인 스크립트 추가
    cmd.append(str(MAIN_SCRIPT))
    
    return cmd 