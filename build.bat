@echo off
chcp 65001 > nul
echo 🚀 Smart Mailbox Windows 빌드 시작
echo.

:: Python 설치 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo    Python 3.11 이상을 설치해주세요: https://python.org
    pause
    exit /b 1
)

:: pip 업그레이드
echo 📦 pip 업그레이드 중...
python -m pip install --upgrade pip

:: 프로젝트 의존성 설치
echo 📦 프로젝트 의존성 설치 중...
pip install -e .

:: PyInstaller 설치
echo 📦 PyInstaller 설치 중...
pip install pyinstaller

:: 빌드 실행
echo 🔨 빌드 시작...
python build_windows.py

if errorlevel 1 (
    echo.
    echo ❌ 빌드가 실패했습니다.
    pause
    exit /b 1
)

echo.
echo ✅ 빌드 완료!
echo 📁 생성된 파일은 releases 폴더에서 확인할 수 있습니다.
echo.

:: releases 폴더 열기 (선택사항)
set /p choice="releases 폴더를 열까요? (y/N): "
if /i "%choice%"=="y" (
    explorer releases
)

pause 