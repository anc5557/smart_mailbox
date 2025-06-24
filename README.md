# 🤖 AI Smart Mailbox

> AI 기반 이메일 자동 분석 및 답장 생성 데스크탑 애플리케이션

## 📌 개요

AI Smart Mailbox는 `.eml` 이메일 파일을 드래그 앤 드롭으로 업로드하면, 로컬 LLM(Ollama)을 통해 자동으로 태깅하고 필요시 답장을 생성해주는 스마트 메일 분석 도구입니다.

### ✨ 주요 기능

- 🎯 **AI 자동 태깅**: 중요, 회신필요, 스팸, 광고 자동 분류
- 💬 **AI 답장 생성**: 회신이 필요한 이메일에 대한 자동 답장 작성
- 🏷️ **커스텀 태그**: 사용자 정의 태그 및 프롬프트 설정
- 🔒 **프라이버시 보장**: 모든 데이터 로컬 처리 (Ollama 사용)
- 🖥️ **크로스 플랫폼**: Windows (.exe), macOS (.dmg) 지원

## 🛠️ 기술 스택

- **언어**: Python 3.13
- **패키지 관리**: uv
- **AI 프레임워크**: LangChain, LangGraph
- **LLM**: Ollama (로컬)
- **GUI**: PyQt6
- **데이터베이스**: SQLAlchemy

## 🚀 설치 및 실행

### 개발 환경 설정

1. **Python 3.13 설치** (필수)
   
2. **uv 설치**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **프로젝트 클론 및 의존성 설치**
   ```bash
   git clone <repository-url>
   cd smart_mailbox
   uv sync
   ```

4. **Ollama 설치 및 실행** (필수)
   ```bash
   # Ollama 설치 (https://ollama.ai)
   # macOS
   brew install ollama
   
   # 또는 공식 웹사이트에서 다운로드
   
   # 모델 다운로드 (예: llama2)
   ollama pull llama2
   
   # Ollama 서버 실행
   ollama serve
   ```

5. **애플리케이션 실행**
   ```bash
   uv run python main.py
   ```

### 배포용 빌드

```bash
# 개발 의존성 설치
uv sync --group dev --group build

# Windows 빌드
uv run python scripts/build_windows.py

# macOS 빌드  
uv run python scripts/build_macos.py
```

## 📁 프로젝트 구조

```
smart_mailbox/
├── src/
│   ├── gui/                 # GUI 컴포넌트
│   ├── ai/                  # AI 처리 모듈
│   ├── email/               # 이메일 처리
│   ├── storage/             # 데이터 관리
│   └── config/              # 설정 관리
├── tests/                   # 테스트
├── assets/                  # 리소스
├── scripts/                 # 빌드 스크립트
└── dist/                    # 배포 파일
```

## 🎯 사용법

1. **Ollama 설정**: 설정 메뉴에서 Ollama 서버 URL 및 모델 설정
2. **이메일 업로드**: `.eml` 파일을 메인 화면에 드래그 앤 드롭
3. **자동 분석**: AI가 자동으로 태그를 분류하고 답장 필요 여부 판단
4. **답장 생성**: 회신이 필요한 이메일에 대해 AI 답장 확인 및 수정
5. **태그 관리**: 사이드바에서 태그별로 이메일 분류 및 관리

## 🔧 개발

### 개발 환경 실행

```bash
# 가상환경 활성화 및 개발 모드 실행
uv run python main.py

# 테스트 실행
uv run pytest

# 코드 포맷팅
uv run black .

# 타입 체크
uv run mypy .
```

### 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 로드맵

- [x] 프로젝트 초기 설정
- [ ] 기본 GUI 구현
- [ ] .eml 파일 파싱
- [ ] Ollama 연결
- [ ] 자동 태깅 시스템
- [ ] AI 답장 생성
- [ ] 커스텀 태그 기능
- [ ] Windows/macOS 빌드

## 🔒 보안 및 프라이버시

- 모든 이메일 데이터는 로컬에서만 처리됩니다
- Ollama를 통한 로컬 LLM 사용으로 외부 데이터 전송 없음
- 사용자 설정 및 민감한 데이터는 암호화하여 저장

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🤝 지원

문제가 발생하거나 기능 요청이 있으시면 [Issues](https://github.com/username/smart_mailbox/issues)에 등록해 주세요.
