#!/usr/bin/env python3
"""
Smart Mailbox 크로스 플랫폼 빌드 스크립트
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from build_config import (
    APP_NAME, APP_VERSION, DIST_DIR, BUILD_DIR, 
    get_pyinstaller_command, PROJECT_ROOT
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

def install_build_dependencies():
    """빌드에 필요한 의존성 설치"""
    print("📦 빌드 의존성 확인 중...")
    
    try:
        # uv 환경인지 확인
        if shutil.which("uv") and "/.venv/" in sys.executable:
            print("   uv 환경 감지됨")
            # pyproject.toml에 이미 pyinstaller가 있는지 확인
            try:
                subprocess.run([sys.executable, "-c", "import PyInstaller"], 
                             check=True, capture_output=True)
                print("   ✓ PyInstaller가 이미 설치되어 있음")
                return True
            except subprocess.CalledProcessError:
                print("   PyInstaller 설치 중...")
                subprocess.run(["uv", "add", "pyinstaller", "--dev"], check=True)
                print("   ✓ PyInstaller 설치 완료")
                return True
        else:
            # 일반 pip 환경
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "pyinstaller>=6.3.0", "wheel", "setuptools"
            ], check=True)
            print("   ✓ PyInstaller 설치 완료")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 의존성 설치 실패: {e}")
        return False
    
    return True

def build_executable(platform_target="auto"):
    """실행 파일 빌드"""
    print(f"🔨 {platform_target} 플랫폼용 실행 파일 빌드 중...")
    
    try:
        cmd = get_pyinstaller_command(platform_target)
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

def create_dmg_for_macos():
    """macOS용 DMG 파일 생성"""
    if platform.system() != "Darwin":
        print("⚠️  macOS가 아니므로 DMG 생성을 건너뜁니다")
        return True
    
    print("📦 macOS DMG 파일 생성 중...")
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    dmg_path = DIST_DIR / f"{APP_NAME}-{APP_VERSION}.dmg"
    
    if not app_path.exists():
        print(f"   ❌ 앱 파일을 찾을 수 없습니다: {app_path}")
        return False
    
    try:
        # 임시 DMG 마운트 포인트 생성
        temp_dmg = DIST_DIR / "temp.dmg"
        
        # DMG 생성 명령어
        cmd = [
            "hdiutil", "create",
            "-srcfolder", str(app_path),
            "-volname", APP_NAME,
            "-fs", "HFS+",
            "-fsargs", "-c c=64,a=16,e=16",
            "-format", "UDRW",
            str(temp_dmg)
        ]
        
        subprocess.run(cmd, check=True)
        
        # 압축된 최종 DMG 생성
        cmd = [
            "hdiutil", "convert", str(temp_dmg),
            "-format", "UDZO",
            "-imagekey", "zlib-level=9",
            "-o", str(dmg_path)
        ]
        
        subprocess.run(cmd, check=True)
        
        # 임시 파일 정리
        if temp_dmg.exists():
            temp_dmg.unlink()
        
        print(f"   ✓ DMG 생성 완료: {dmg_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ DMG 생성 실패: {e}")
        return False

def organize_final_builds():
    """최종 빌드 파일들을 정리된 폴더에 배치"""
    print("📁 최종 빌드 파일 정리 중...")
    
    final_dir = PROJECT_ROOT / "releases"
    final_dir.mkdir(exist_ok=True)
    
    # 기존 파일들 정리
    for file in final_dir.glob("*"):
        if file.is_file():
            file.unlink()
    
    current_platform = platform.system()
    
    if current_platform == "Windows":
        # Windows exe 파일 복사
        exe_file = DIST_DIR / f"{APP_NAME}.exe"
        if exe_file.exists():
            target = final_dir / f"{APP_NAME}-{APP_VERSION}-Windows.exe"
            shutil.copy2(exe_file, target)
            print(f"   ✓ Windows 빌드: {target}")
    
    elif current_platform == "Darwin":
        # macOS DMG 파일 복사
        dmg_file = DIST_DIR / f"{APP_NAME}-{APP_VERSION}.dmg"
        if dmg_file.exists():
            target = final_dir / f"{APP_NAME}-{APP_VERSION}-macOS.dmg"
            shutil.copy2(dmg_file, target)
            print(f"   ✓ macOS 빌드: {target}")
    
    print(f"\n🎉 최종 빌드 파일들이 {final_dir} 폴더에 준비되었습니다!")
    
    # 파일 목록 출력
    print("\n📋 생성된 파일들:")
    for file in final_dir.glob("*"):
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   • {file.name} ({size_mb:.1f} MB)")

def main():
    """메인 빌드 함수"""
    print(f"🚀 Smart Mailbox v{APP_VERSION} 빌드 시작")
    print(f"🖥️  현재 플랫폼: {platform.system()} {platform.machine()}")
    print(f"🐍 Python 버전: {sys.version}")
    print("=" * 60)
    
    # 1. 이전 빌드 정리
    clean_build_dirs()
    
    # 2. 의존성 설치
    if not install_build_dependencies():
        return 1
    
    # 3. 실행 파일 빌드
    if not build_executable():
        return 1
    
    # 4. macOS DMG 생성 (macOS인 경우)
    if platform.system() == "Darwin":
        if not create_dmg_for_macos():
            return 1
    
    # 5. 최종 파일 정리
    organize_final_builds()
    
    print("\n✅ 빌드 완료!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 