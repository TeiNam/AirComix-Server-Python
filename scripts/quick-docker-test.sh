#!/bin/bash

# 빠른 Docker 빌드 테스트
# 기본 Docker 명령어만 사용하는 간단한 테스트

set -e

echo "🚀 빠른 Docker 빌드 테스트"
echo "========================="

# 현재 디렉토리 확인
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml 파일을 찾을 수 없습니다."
    echo "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

echo "📦 프로덕션 이미지 빌드 중..."
docker build -f docker/Dockerfile -t aircomix-server:quick-test . --no-cache

echo "✅ 빌드 성공!"
echo ""

echo "📊 이미지 정보:"
docker images aircomix-server:quick-test

echo ""
echo "🧹 테스트 이미지 정리 중..."
docker rmi aircomix-server:quick-test

echo "🎉 테스트 완료!"