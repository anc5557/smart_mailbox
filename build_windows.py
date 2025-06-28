#!/usr/bin/env python3
"""
Smart Mailbox Windows 전용 빌드 스크립트
이 스크립트는 Windows 환경에서 실행되어야 합니다.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from build_config import (
    APP_NAME, APP_VERSION, DIST_DIR, BUILD_DIR, 
    PROJECT_ROOT, SRC_DIR, MAIN_SCRIPT, HIDDEN_IMPORTS
)

def clean_build_dirs():
    """빌드 디렉토리 정리"""
    print("🧹 이전 빌드 파일 정리 중...")
    
    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   ✓ 삭제됨: {dir_path}")
    
    # spec 파일들도 정리
    for spec_file in PROJECT_ROOT.glob("*.spec"):
        spec_file.unlink()
        print(f"   ✓ 삭제됨: {spec_file}")

def install_dependencies():
    """Windows 빌드에 필요한 의존성 설치"""
    print("📦 Windows 빌드 의존성 설치 중...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pyinstaller>=6.3.0", "wheel", "setuptools"
        ], check=True)
        print("   ✓ PyInstaller 설치 완료")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 의존성 설치 실패: {e}")
        return False
    
    return True

def build_windows_exe():
    """Windows 실행 파일 빌드"""
    print("🔨 Windows 실행 파일 빌드 중...")
    
    # PyInstaller 명령어 구성
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        "--add-data", f"{SRC_DIR};.",
    ]
    
    # 숨겨진 임포트 추가
    for module in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module])
    
    # Windows 전용 옵션
    version_file = PROJECT_ROOT / "version_info.txt"
    if version_file.exists():
        cmd.extend(["--version-file", str(version_file)])
    
    # 아이콘 추가 (있는 경우)
    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # 메인 스크립트
    cmd.append(str(MAIN_SCRIPT))
    
    try:
        print(f"   실행 명령어: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("   ✓ PyInstaller 빌드 성공")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 빌드 실패: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def organize_windows_build():
    """Windows 빌드 결과 정리"""
    print("📁 Windows 빌드 파일 정리 중...")
    
    final_dir = PROJECT_ROOT / "releases"
    final_dir.mkdir(exist_ok=True)
    
    # 기존 Windows 파일 정리
    for file in final_dir.glob("*Windows*"):
        if file.is_file():
            file.unlink()
    
    # Windows exe 파일 복사
    exe_file = DIST_DIR / f"{APP_NAME}.exe"
    if exe_file.exists():
        target = final_dir / f"{APP_NAME}-{APP_VERSION}-Windows.exe"
        shutil.copy2(exe_file, target)
        print(f"   ✓ Windows 빌드: {target}")
        
        # 파일 크기 정보
        size_mb = target.stat().st_size / (1024 * 1024)
        print(f"   📦 파일 크기: {size_mb:.1f} MB")
    else:
        print(f"   ❌ 실행 파일을 찾을 수 없습니다: {exe_file}")
        return False
    
    return True

def main():
    """메인 Windows 빌드 함수"""
    if platform.system() != "Windows":
        print("❌ 이 스크립트는 Windows에서만 실행할 수 있습니다.")
        print("   현재 플랫폼:", platform.system())
        return 1
    
    print(f"🪟 Smart Mailbox v{APP_VERSION} Windows 빌드 시작")
    print(f"🖥️  플랫폼: {platform.system()} {platform.machine()}")
    print(f"🐍 Python 버전: {sys.version}")
    print("=" * 60)
    
    # 1. 이전 빌드 정리
    clean_build_dirs()
    
    # 2. 의존성 설치
    if not install_dependencies():
        return 1
    
    # 3. Windows 실행 파일 빌드
    if not build_windows_exe():
        return 1
    
    # 4. 빌드 결과 정리
    if not organize_windows_build():
        return 1
    
    print("\n✅ Windows 빌드 완료!")
    print("\n📋 생성된 파일:")
    
    final_dir = PROJECT_ROOT / "releases"
    for file in final_dir.glob("*Windows*"):
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   • {file.name} ({size_mb:.1f} MB)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 