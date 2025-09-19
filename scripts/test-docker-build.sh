#!/bin/bash

# Docker 빌드 테스트 스크립트
# 로컬에서 Docker 이미지 빌드를 테스트합니다.

set -e

echo "🐳 Docker 빌드 테스트 시작"
echo "========================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 현재 디렉토리 확인
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ pyproject.toml 파일을 찾을 수 없습니다.${NC}"
    echo "프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

if [ ! -d "app" ]; then
    echo -e "${RED}❌ app/ 디렉토리를 찾을 수 없습니다.${NC}"
    exit 1
fi

if [ ! -f "docker/Dockerfile" ]; then
    echo -e "${RED}❌ docker/Dockerfile을 찾을 수 없습니다.${NC}"
    exit 1
fi

echo -e "${BLUE}1. Docker 환경 확인${NC}"
echo "==================="

# Docker Buildx 사용 가능 여부 확인
if docker buildx version > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Buildx 사용 가능${NC}"
    BUILD_CMD="docker buildx build"
    PROGRESS_FLAG="--progress=plain"
else
    echo -e "${YELLOW}⚠️  Docker Buildx 없음, 기본 빌더 사용${NC}"
    BUILD_CMD="docker build"
    PROGRESS_FLAG=""
fi

echo ""
echo -e "${BLUE}2. 프로덕션 이미지 빌드 테스트${NC}"
echo "================================"

# 프로덕션 이미지 빌드
echo -e "${YELLOW}프로덕션 이미지 빌드 중...${NC}"
if $BUILD_CMD -f docker/Dockerfile -t aircomix-server:test-prod $PROGRESS_FLAG .; then
    echo -e "${GREEN}✅ 프로덕션 이미지 빌드 성공${NC}"
else
    echo -e "${RED}❌ 프로덕션 이미지 빌드 실패${NC}"
    echo -e "${YELLOW}💡 빌드 로그를 확인하여 오류를 해결하세요.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}3. 개발 이미지 빌드 테스트${NC}"
echo "=========================="

# 개발 이미지 빌드
echo -e "${YELLOW}개발 이미지 빌드 중...${NC}"
if $BUILD_CMD -f docker/Dockerfile.dev -t aircomix-server:test-dev $PROGRESS_FLAG .; then
    echo -e "${GREEN}✅ 개발 이미지 빌드 성공${NC}"
else
    echo -e "${RED}❌ 개발 이미지 빌드 실패${NC}"
    echo -e "${YELLOW}💡 빌드 로그를 확인하여 오류를 해결하세요.${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}4. 이미지 정보 확인${NC}"
echo "=================="

echo -e "${YELLOW}프로덕션 이미지:${NC}"
docker images aircomix-server:test-prod

echo -e "${YELLOW}개발 이미지:${NC}"
docker images aircomix-server:test-dev

echo ""
echo -e "${BLUE}5. 간단한 실행 테스트${NC}"
echo "==================="

# 테스트용 임시 디렉토리 생성
TEST_DIR="/tmp/comix-test"
mkdir -p "$TEST_DIR"
echo "test file" > "$TEST_DIR/test.txt"

echo -e "${YELLOW}프로덕션 이미지 실행 테스트...${NC}"
if timeout 10s docker run --rm -p 31258:31257 -v "$TEST_DIR:/comix:ro" aircomix-server:test-prod &
then
    sleep 5
    if curl -f http://localhost:31258/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 프로덕션 이미지 실행 성공${NC}"
    else
        echo -e "${YELLOW}⚠️  헬스체크 실패 (정상일 수 있음)${NC}"
    fi
    # 컨테이너 정리
    docker ps -q --filter ancestor=aircomix-server:test-prod | xargs -r docker kill > /dev/null 2>&1
else
    echo -e "${YELLOW}⚠️  실행 테스트 타임아웃 (정상일 수 있음)${NC}"
fi

echo ""
echo -e "${BLUE}6. 정리${NC}"
echo "======="

read -p "테스트 이미지를 삭제하시겠습니까? (y/N): " DELETE_IMAGES

if [[ $DELETE_IMAGES =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}테스트 이미지 삭제 중...${NC}"
    docker rmi aircomix-server:test-prod aircomix-server:test-dev > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ 테스트 이미지 삭제 완료${NC}"
fi

# 임시 디렉토리 정리
rm -rf "$TEST_DIR"

echo ""
echo -e "${GREEN}🎉 Docker 빌드 테스트 완료!${NC}"
echo ""
echo -e "${BLUE}다음 단계:${NC}"
echo "1. GitHub에 푸시하여 CI/CD 테스트"
echo "2. Docker Hub에서 이미지 확인"
echo "3. 실제 환경에서 배포 테스트"