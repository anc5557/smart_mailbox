#!/bin/bash

echo "🚀 Smart Mailbox 빌드 시작"
echo "🖥️  플랫폼: $(uname -s) $(uname -m)"

# Python 설치 확인
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python이 설치되지 않았습니다."
        echo "   Python 3.11 이상을 설치해주세요."
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "🐍 Python 버전: $($PYTHON_CMD --version)"

# 가상환경 확인 (uv 또는 venv)
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "📦 가상환경 감지됨: $VIRTUAL_ENV"
elif command -v uv &> /dev/null && [[ -d ".venv" ]]; then
    echo "📦 uv 환경 감지됨"
    PYTHON_CMD="uv run python"
fi

# 빌드 실행
echo "🔨 빌드 시작..."
$PYTHON_CMD build.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 빌드 완료!"
    echo "📁 생성된 파일은 releases 폴더에서 확인할 수 있습니다."
    echo ""
    
    # releases 폴더 내용 표시
    if [ -d "releases" ]; then
        echo "📋 생성된 파일들:"
        ls -lh releases/
        echo ""
        
        # macOS인 경우 Finder로 열기 제안
        if [[ "$(uname -s)" == "Darwin" ]]; then
            read -p "Finder에서 releases 폴더를 열까요? (y/N): " choice
            if [[ "$choice" =~ ^[Yy]$ ]]; then
                open releases/
            fi
        fi
    fi
else
    echo ""
    echo "❌ 빌드가 실패했습니다."
    echo "   오류를 확인하고 다시 시도해주세요."
    exit 1
fi 