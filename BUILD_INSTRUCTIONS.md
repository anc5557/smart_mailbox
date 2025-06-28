# Smart Mailbox 빌드 가이드

이 문서는 Smart Mailbox 애플리케이션을 Windows 실행 파일(.exe)과 macOS 애플리케이션(.dmg)으로 빌드하는 방법을 설명합니다.

## 🚀 빠른 빌드

### 현재 플랫폼용 빌드
```bash
python build.py
```

### 크로스 플랫폼 빌드 (Docker 필요)
```bash
python build_cross_platform.py
```

## 📋 사전 요구사항

### 기본 요구사항
- Python 3.11 이상
- 프로젝트 의존성 (`pip install -e .`)

### Windows 빌드
- Windows 10/11
- PyInstaller (`pip install pyinstaller`)

### macOS 빌드
- macOS 10.15 (Catalina) 이상
- Xcode Command Line Tools
- PyInstaller (`pip install pyinstaller`)

### 크로스 플랫폼 빌드
- Docker Desktop (Windows 빌드용)
- macOS (macOS 빌드용)

## 📦 빌드 방법

### 1. 단일 플랫폼 빌드

#### Windows에서 Windows 빌드
```bash
# 의존성 설치
pip install -e .
pip install pyinstaller

# 빌드 실행
python build.py
```

#### macOS에서 macOS 빌드
```bash
# 의존성 설치
pip install -e .
pip install pyinstaller

# 빌드 실행
python build.py
```

### 2. 크로스 플랫폼 빌드

#### macOS에서 Windows + macOS 빌드
```bash
# Docker Desktop 설치 및 실행 확인
docker --version

# 크로스 플랫폼 빌드 실행
python build_cross_platform.py
```

### 3. PyInstaller 스펙 파일 사용
```bash
# 스펙 파일로 직접 빌드
pyinstaller smart_mailbox.spec
```

## 📁 빌드 결과물

빌드가 완료되면 `releases/` 폴더에 다음 파일들이 생성됩니다:

### Windows
- `Smart Mailbox-0.1.0-Windows.exe` - Windows 실행 파일

### macOS  
- `Smart Mailbox-0.1.0-macOS.dmg` - macOS 설치 파일

## 🔧 빌드 옵션 커스터마이징

### build_config.py 수정
빌드 설정을 변경하려면 `build_config.py` 파일을 수정하세요:

```python
# 앱 정보
APP_NAME = "Smart Mailbox"
APP_VERSION = "0.1.0"

# PyInstaller 옵션
PYINSTALLER_OPTIONS = [
    "--name", APP_NAME,
    "--onefile",        # 단일 파일로 빌드
    "--windowed",       # 콘솔 창 숨기기
    "--noconfirm",      # 기존 파일 덮어쓰기
    "--clean",          # 빌드 전 정리
]
```

### 아이콘 추가
아이콘을 추가하려면 `assets/` 폴더에 다음 파일들을 배치하세요:
- `icon.ico` - Windows용 아이콘
- `icon.icns` - macOS용 아이콘

## 🐛 문제 해결

### 1. 빌드 실패 시
```bash
# 빌드 캐시 정리
rm -rf build/ dist/ *.spec

# 의존성 재설치
pip uninstall pyinstaller
pip install pyinstaller

# 다시 빌드
python build.py
```

### 2. 모듈 import 오류
`build_config.py`의 `HIDDEN_IMPORTS`에 누락된 모듈을 추가하세요:

```python
HIDDEN_IMPORTS = [
    "PyQt6.QtCore",
    "PyQt6.QtWidgets",
    # 추가 모듈...
]
```

### 3. macOS 권한 문제
```bash
# 앱 서명 (개발용)
codesign --force --deep --sign - "dist/Smart Mailbox.app"

# Gatekeeper 우회 (테스트용)
sudo xattr -dr com.apple.quarantine "dist/Smart Mailbox.app"
```

### 4. Windows Defender 경고
빌드된 exe 파일이 Windows Defender에 의해 차단될 수 있습니다. 이는 PyInstaller로 만든 실행 파일의 일반적인 문제입니다. 해결 방법:

1. Windows Defender 예외 추가
2. 코드 서명 인증서 사용
3. 배포 전 충분한 테스트

## 🚀 자동 빌드 (GitHub Actions)

프로젝트에 GitHub Actions 워크플로우가 설정되어 있어 다음과 같이 자동 빌드됩니다:

1. `main` 브랜치에 푸시 시 자동 빌드
2. 태그 생성 시 릴리스 자동 생성
3. Windows와 macOS 빌드 병렬 실행

### 릴리스 생성
```bash
git tag v0.1.0
git push origin v0.1.0
```

## 📞 지원

빌드 관련 문제가 있으면 GitHub Issues에 문의하세요.

- 빌드 환경 정보 (OS, Python 버전)
- 오류 메시지 전문
- 실행한 명령어 