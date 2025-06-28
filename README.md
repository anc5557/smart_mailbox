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
- **데이터 저장**: JSON 기반 파일 시스템

## 🚀 설치 및 실행

### 📦 미리 빌드된 버전 사용 (추천)

1. [Releases 페이지](../../releases)에서 최신 버전을 다운로드하세요
   - **Windows**: `Smart Mailbox-x.x.x-Windows.exe`
   - **macOS**: `Smart Mailbox-x.x.x-macOS.dmg`

2. 다운로드한 파일을 실행하면 바로 사용할 수 있습니다

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
   git clone https://github.com/your-username/smart_mailbox.git
   cd smart_mailbox
   uv sync
   ```

4. **Ollama 설치 및 실행** (필수)
   ```bash
   # Ollama 설치 (https://ollama.ai)
   # macOS
   brew install ollama
   
   # 또는 공식 웹사이트에서 다운로드
   
   # 모델 다운로드 (예: llama3.2)
   ollama pull llama3.2
   
   # Ollama 서버 실행 (백그라운드)
   ollama serve
   ```

5. **애플리케이션 실행**
   ```bash
   # 메인 애플리케이션 실행
   uv run python src/smart_mailbox/main.py
   
   # 또는 프로젝트 루트에서
   uv run python -m smart_mailbox.main
   ```

### 🔨 직접 빌드하기

#### 간단한 방법
```bash
# Windows에서
build.bat

# macOS/Linux에서  
./build.sh
```

#### 상세 빌드 옵션
```bash
# 현재 플랫폼용 빌드
python build.py

# Windows 전용 빌드 (Windows에서)
python build_windows.py

# 크로스 플랫폼 빌드 (Docker 필요)
python build_cross_platform.py
```

빌드된 파일은 `releases/` 폴더에 생성됩니다.

## 📁 프로젝트 구조

```
smart_mailbox/
├── src/
│   └── smart_mailbox/
│       ├── main.py          # 메인 진입점
│       ├── gui/             # GUI 컴포넌트
│       │   ├── main_window.py
│       │   ├── email_view.py
│       │   ├── sidebar.py
│       │   └── settings.py
│       ├── ai/              # AI 처리 모듈
│       │   ├── ollama_client.py
│       │   ├── tagger.py
│       │   └── reply_gen.py
│       ├── email/           # 이메일 처리
│       │   └── parser.py
│       ├── storage/         # 데이터 관리
│       │   ├── json_storage.py
│       │   └── file_manager.py
│       └── config/          # 설정 관리
│           ├── ai.py
│           ├── tags.py
│           └── logger.py
├── assets/                  # 리소스 파일
├── releases/                # 빌드된 실행 파일
├── build*.py               # 빌드 스크립트들
├── pyproject.toml          # 프로젝트 설정
└── README.md               # 이 파일
```

## 🎯 사용법

1. **Ollama 설정**: 
   - Ollama 서버가 실행 중인지 확인 (`ollama serve`)
   - 설정 메뉴에서 Ollama 서버 URL 및 모델 설정

2. **이메일 업로드**: 
   - `.eml` 파일을 메인 화면에 드래그 앤 드롭
   - 또는 파일 메뉴에서 직접 선택

3. **자동 분석**: 
   - AI가 자동으로 태그를 분류하고 답장 필요 여부 판단
   - 분석 결과는 사이드바에서 확인

4. **답장 생성**: 
   - 회신이 필요한 이메일에 대해 AI 답장 확인 및 수정
   - 생성된 답장은 편집 가능

5. **태그 관리**: 
   - 사이드바에서 태그별로 이메일 분류 및 관리
   - 커스텀 태그 추가 및 수정 가능

## 🔧 개발

### 개발 환경 실행

```bash
# 개발 모드로 실행
uv run python src/smart_mailbox/main.py

# 타입 체크 (mypy 설치 후)
uv add mypy --dev
uv run mypy src/

# 코드 포맷팅 (black 설치 후)
uv add black --dev
uv run black src/

# 린팅 (ruff 설치 후)
uv add ruff --dev
uv run ruff check src/
```

### 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 로드맵

### ✅ 완료된 기능
- [x] 프로젝트 초기 설정 및 구조 설계
- [x] 기본 GUI 프레임워크 구현 (PyQt6)
- [x] .eml 파일 파싱 시스템
- [x] Ollama 클라이언트 연결
- [x] 자동 태깅 시스템 (AI 기반)
- [x] AI 답장 생성 엔진
- [x] 로컬 데이터 저장 시스템 (JSON)
- [x] 설정 관리 시스템
- [x] Windows/macOS 빌드 시스템
- [x] 크로스 플랫폼 배포 자동화

### 🚧 개발 중
- [ ] GUI 컴포넌트 완성 및 사용자 경험 개선
- [ ] 이메일 뷰어 상세 기능 구현
- [ ] 사이드바 태그 관리 시스템
- [ ] 설정 화면 UI/UX 완성

### 🎯 예정된 기능
- [ ] 커스텀 태그 및 프롬프트 편집 기능
- [ ] 이메일 검색 및 필터링
- [ ] 대량 이메일 배치 처리
- [ ] 태그별 통계 및 리포트
- [ ] 이메일 첨부파일 처리
- [ ] 다국어 지원 (한국어, 영어)
- [ ] 테마 커스터마이징
- [ ] 플러그인 시스템

### 🔮 장기 계획
- [ ] 클라우드 동기화 지원
- [ ] 모바일 앱 연동
- [ ] 웹 인터페이스 제공
- [ ] 머신러닝 모델 개선
- [ ] 엔터프라이즈 기능 (팀 공유, 권한 관리)
- [ ] API 서버 모드

## 🔒 보안 및 프라이버시

- 모든 이메일 데이터는 로컬에서만 처리됩니다
- Ollama를 통한 로컬 LLM 사용으로 외부 데이터 전송 없음
- 사용자 설정 및 민감한 데이터는 로컬 파일에 안전하게 저장

## 🐛 문제 해결

### 일반적인 문제들

1. **Ollama 연결 오류**
   ```bash
   # Ollama 서버 상태 확인
   ollama list
   
   # 서버 재시작
   ollama serve
   ```

2. **Python 버전 호환성**
   - Python 3.13 이상 필수
   - `python --version`으로 버전 확인

3. **GUI 실행 오류**
   - PyQt6 설치 확인: `uv add PyQt6`
   - 디스플레이 설정 확인 (Linux의 경우)

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원 및 연락

- 이슈 리포트: [GitHub Issues](../../issues)
- 기능 요청: [GitHub Discussions](../../discussions)
- 이메일: your-email@example.com

---

⭐ 이 프로젝트가 유용하다면 스타를 눌러주세요!
