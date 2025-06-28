#!/usr/bin/env python3
"""
Smart Mailbox 크로스 플랫폼 빌드 스크립트 (Docker 기반)
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from build_config import APP_NAME, APP_VERSION, PROJECT_ROOT

def check_docker():
    """Docker 설치 및 실행 상태 확인"""
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Docker 확인됨: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker가 설치되지 않았거나 실행되지 않습니다.")
        print("   Docker Desktop을 설치하고 실행해주세요: https://www.docker.com/products/docker-desktop")
        return False

def build_windows_in_docker():
    """Docker에서 Windows 빌드 실행"""
    print("🐳 Docker에서 Windows 빌드 시작...")
    
    dockerfile_content = '''FROM python:3.11-windowsservercore

# 작업 디렉토리 설정
WORKDIR /app

# 프로젝트 파일 복사
COPY . .

# 의존성 설치
RUN pip install -r requirements.txt
RUN pip install pyinstaller

# 빌드 실행
RUN python build.py

# 결과물 복사를 위한 볼륨 설정
VOLUME ["/app/releases"]
'''
    
    # Dockerfile 생성
    dockerfile_path = PROJECT_ROOT / "Dockerfile.windows"
    with open(dockerfile_path, 'w') as f:
        f.write(dockerfile_content)
    
    try:
        # Docker 이미지 빌드
        print("   📦 Windows 빌드 이미지 생성 중...")
        subprocess.run([
            "docker", "build", 
            "-f", str(dockerfile_path),
            "-t", "smart-mailbox-windows-build", 
            "."
        ], check=True, cwd=PROJECT_ROOT)
        
        # 컨테이너 실행 및 빌드
        print("   🔨 Windows 실행파일 빌드 중...")
        releases_dir = PROJECT_ROOT / "releases"
        releases_dir.mkdir(exist_ok=True)
        
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{releases_dir}:/app/releases",
            "smart-mailbox-windows-build"
        ], check=True)
        
        print("   ✓ Windows 빌드 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Windows Docker 빌드 실패: {e}")
        return False
    finally:
        # Dockerfile 정리
        if dockerfile_path.exists():
            dockerfile_path.unlink()

def build_macos_native():
    """네이티브 macOS 빌드"""
    if platform.system() != "Darwin":
        print("⚠️  macOS 빌드는 macOS에서만 가능합니다.")
        return False
    
    print("🍎 네이티브 macOS 빌드 시작...")
    
    try:
        subprocess.run([sys.executable, "build.py"], check=True, cwd=PROJECT_ROOT)
        print("   ✓ macOS 빌드 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ macOS 빌드 실패: {e}")
        return False

def create_requirements_txt():
    """requirements.txt 파일 생성 (Docker 빌드용)"""
    print("📝 requirements.txt 생성 중...")
    
    requirements_content = '''# AI/LLM 라이브러리
langchain>=0.1.0
langchain-community>=0.0.10
langgraph>=0.0.30

# 이메일 처리
email-validator>=2.1.0
chardet>=5.2.0

# GUI 프레임워크  
PyQt6>=6.4.0
PyQt6-tools>=6.4.0

# Ollama 연결용
ollama>=0.5.1

# 유틸리티
pydantic>=2.5.0
python-dotenv>=1.0.0
typer>=0.9.0
rich>=13.7.0

# 암호화
cryptography>=41.0.0
pyqtdarktheme>=2.1.0
pathvalidate>=3.0.0

# 빌드 도구
pyinstaller>=6.3.0
wheel
setuptools
'''
    
    requirements_path = PROJECT_ROOT / "requirements.txt"
    with open(requirements_path, 'w') as f:
        f.write(requirements_content)
    
    print(f"   ✓ {requirements_path} 생성됨")

def organize_cross_platform_builds():
    """크로스 플랫폼 빌드 결과 정리"""
    print("📁 크로스 플랫폼 빌드 결과 정리 중...")
    
    releases_dir = PROJECT_ROOT / "releases"
    releases_dir.mkdir(exist_ok=True)
    
    print(f"\n🎉 최종 빌드 파일들이 {releases_dir} 폴더에 준비되었습니다!")
    
    # 파일 목록 출력
    files = list(releases_dir.glob("*"))
    if files:
        print("\n📋 생성된 파일들:")
        for file in files:
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   • {file.name} ({size_mb:.1f} MB)")
    else:
        print("   ⚠️  생성된 파일이 없습니다.")

def main():
    """메인 크로스 플랫폼 빌드 함수"""
    print(f"🌍 Smart Mailbox v{APP_VERSION} 크로스 플랫폼 빌드 시작")
    print(f"🖥️  현재 플랫폼: {platform.system()} {platform.machine()}")
    print("=" * 70)
    
    current_platform = platform.system()
    success_count = 0
    
    # requirements.txt 생성
    create_requirements_txt()
    
    # 1. Windows 빌드 (Docker 사용)
    if current_platform != "Windows":
        if check_docker():
            if build_windows_in_docker():
                success_count += 1
        else:
            print("⚠️  Docker를 사용할 수 없어 Windows 빌드를 건너뜁니다.")
    else:
        # Windows에서는 네이티브 빌드
        try:
            subprocess.run([sys.executable, "build.py"], check=True)
            success_count += 1
        except subprocess.CalledProcessError:
            print("❌ Windows 네이티브 빌드 실패")
    
    # 2. macOS 빌드 (네이티브만 가능)
    if current_platform == "Darwin":
        if build_macos_native():
            success_count += 1
    else:
        print("⚠️  macOS 빌드는 macOS에서만 가능합니다.")
    
    # 3. 결과 정리
    organize_cross_platform_builds()
    
    print(f"\n{'='*70}")
    print(f"✅ 크로스 플랫폼 빌드 완료! ({success_count}개 플랫폼 성공)")
    
    if success_count == 0:
        print("❌ 모든 플랫폼 빌드가 실패했습니다.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 