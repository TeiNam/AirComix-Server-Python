#!/bin/bash

# GitHub Actions 설정 도우미 스크립트
# GitHub Secrets 설정을 위한 가이드를 제공합니다.

set -e

echo "🚀 Comix Server GitHub Actions 설정 도우미"
echo "=========================================="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker Hub 사용자명 확인
echo -e "${BLUE}1. Docker Hub 설정${NC}"
echo "GitHub Actions에서 Docker Hub에 이미지를 배포하려면 다음 정보가 필요합니다:"
echo ""

read -p "Docker Hub 사용자명을 입력하세요: " DOCKER_USERNAME

if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}❌ Docker Hub 사용자명이 필요합니다.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Docker Hub 사용자명: $DOCKER_USERNAME${NC}"
echo ""

# GitHub Secrets 설정 안내
echo -e "${BLUE}2. GitHub Secrets 설정${NC}"
echo "GitHub 저장소의 Settings > Secrets and variables > Actions에서"
echo "다음 secrets을 설정해야 합니다:"
echo ""
echo -e "${YELLOW}필수 Secrets:${NC}"
echo "  DOCKERHUB_USERNAME: $DOCKER_USERNAME"
echo "  DOCKERHUB_TOKEN: [Docker Hub 액세스 토큰]"
echo ""

# Docker Hub 토큰 생성 안내
echo -e "${BLUE}3. Docker Hub 액세스 토큰 생성${NC}"
echo "보안을 위해 비밀번호 대신 액세스 토큰을 사용하는 것을 권장합니다:"
echo ""
echo "1. https://hub.docker.com 로그인"
echo "2. Account Settings > Security > New Access Token"
echo "3. 토큰 이름: 'github-actions'"
echo "4. 권한: Read, Write, Delete 선택"
echo "5. 생성된 토큰을 DOCKERHUB_TOKEN에 설정"
echo ""

# README 업데이트 안내
echo -e "${BLUE}4. README.md 업데이트${NC}"
echo "README.md 파일에서 다음 부분을 실제 사용자명으로 변경하세요:"
echo ""
echo -e "${YELLOW}변경 필요한 부분:${NC}"
echo "  [사용자명] → $DOCKER_USERNAME"
echo ""

# 자동 업데이트 제안
read -p "README.md를 자동으로 업데이트하시겠습니까? (y/N): " UPDATE_README

if [[ $UPDATE_README =~ ^[Yy]$ ]]; then
    if [ -f "README.md" ]; then
        # README.md 백업
        cp README.md README.md.bak
        
        # 사용자명 교체
        sed -i.tmp "s/\[사용자명\]/$DOCKER_USERNAME/g" README.md
        rm README.md.tmp
        
        echo -e "${GREEN}✅ README.md가 업데이트되었습니다.${NC}"
        echo -e "${YELLOW}💡 백업 파일: README.md.bak${NC}"
    else
        echo -e "${RED}❌ README.md 파일을 찾을 수 없습니다.${NC}"
    fi
fi

echo ""

# 워크플로우 파일 확인
echo -e "${BLUE}5. 워크플로우 파일 확인${NC}"
if [ -d ".github/workflows" ]; then
    echo -e "${GREEN}✅ GitHub Actions 워크플로우 파일이 존재합니다:${NC}"
    ls -la .github/workflows/
else
    echo -e "${RED}❌ .github/workflows 디렉토리가 없습니다.${NC}"
    echo "GitHub Actions 워크플로우 파일을 먼저 생성해주세요."
fi

echo ""

# 다음 단계 안내
echo -e "${BLUE}6. 다음 단계${NC}"
echo "1. GitHub Secrets 설정 완료"
echo "2. 코드를 main 브랜치에 푸시"
echo "3. GitHub Actions 탭에서 빌드 상태 확인"
echo "4. Docker Hub에서 이미지 확인"
echo ""

# 유용한 명령어들
echo -e "${BLUE}7. 유용한 명령어들${NC}"
echo ""
echo -e "${YELLOW}로컬 테스트:${NC}"
echo "  make test          # 테스트 실행"
echo "  make build         # Docker 이미지 빌드"
echo "  make run           # 서버 실행"
echo ""
echo -e "${YELLOW}Docker Hub 이미지 사용:${NC}"
echo "  docker pull $DOCKER_USERNAME/aircomix-server:latest"
echo "  docker run -d -p 31257:31257 -v /path/to/comix:/comix:ro $DOCKER_USERNAME/aircomix-server:latest"
echo ""

echo -e "${GREEN}🎉 설정 완료! GitHub Actions가 자동으로 Docker 이미지를 빌드하고 배포합니다.${NC}"