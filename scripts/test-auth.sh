#!/bin/bash

# 인증 기능 테스트 스크립트
# 로컬에서 인증이 올바르게 작동하는지 테스트합니다.

set -e

echo "🔐 Comix Server 인증 테스트"
echo "=========================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 설정
TEST_PORT=31258
TEST_USERNAME="testuser"
TEST_PASSWORD="testpass123"
SERVER_URL="http://localhost:${TEST_PORT}"

echo -e "${BLUE}1. 인증 없이 서버 시작 테스트${NC}"
echo "================================"

# 인증 없는 서버 시작 (백그라운드)
echo -e "${YELLOW}인증 비활성화 상태로 서버 시작 중...${NC}"
COMIX_MANGA_DIRECTORY="/tmp" \
COMIX_SERVER_PORT=${TEST_PORT} \
COMIX_ENABLE_AUTH=false \
python -m app.main &
SERVER_PID=$!

# 서버 시작 대기
sleep 3

# 인증 없이 접근 테스트
echo -e "${YELLOW}인증 없이 접근 테스트...${NC}"
if curl -s -f "${SERVER_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ 인증 없이 접근 성공${NC}"
else
    echo -e "${RED}❌ 인증 없이 접근 실패${NC}"
fi

# 서버 종료
kill $SERVER_PID 2>/dev/null || true
sleep 2

echo ""
echo -e "${BLUE}2. 인증 활성화 서버 테스트${NC}"
echo "=========================="

# 인증 활성화 서버 시작 (백그라운드)
echo -e "${YELLOW}인증 활성화 상태로 서버 시작 중...${NC}"
COMIX_MANGA_DIRECTORY="/tmp" \
COMIX_SERVER_PORT=${TEST_PORT} \
COMIX_ENABLE_AUTH=true \
COMIX_AUTH_USERNAME=${TEST_USERNAME} \
COMIX_AUTH_PASSWORD=${TEST_PASSWORD} \
python -m app.main &
SERVER_PID=$!

# 서버 시작 대기
sleep 3

# 인증 없이 접근 테스트 (실패해야 함)
echo -e "${YELLOW}인증 없이 접근 테스트 (401 에러 예상)...${NC}"
if curl -s -f "${SERVER_URL}/health" > /dev/null; then
    echo -e "${RED}❌ 인증 없이 접근 성공 (문제!)${NC}"
else
    echo -e "${GREEN}✅ 인증 없이 접근 차단됨 (정상)${NC}"
fi

# 잘못된 인증으로 접근 테스트
echo -e "${YELLOW}잘못된 인증으로 접근 테스트...${NC}"
if curl -s -f -u "wrong:password" "${SERVER_URL}/health" > /dev/null; then
    echo -e "${RED}❌ 잘못된 인증으로 접근 성공 (문제!)${NC}"
else
    echo -e "${GREEN}✅ 잘못된 인증 차단됨 (정상)${NC}"
fi

# 올바른 인증으로 접근 테스트
echo -e "${YELLOW}올바른 인증으로 접근 테스트...${NC}"
if curl -s -f -u "${TEST_USERNAME}:${TEST_PASSWORD}" "${SERVER_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ 올바른 인증으로 접근 성공${NC}"
else
    echo -e "${RED}❌ 올바른 인증으로 접근 실패${NC}"
fi

# 제외 경로 테스트 (헬스체크는 인증 없이 접근 가능해야 함)
echo -e "${YELLOW}제외 경로 접근 테스트...${NC}"
if curl -s -f "${SERVER_URL}/health" > /dev/null; then
    echo -e "${GREEN}✅ 헬스체크 경로 접근 성공 (정상)${NC}"
else
    echo -e "${YELLOW}⚠️  헬스체크 경로 접근 실패 (설정 확인 필요)${NC}"
fi

# 서버 종료
kill $SERVER_PID 2>/dev/null || true
sleep 2

echo ""
echo -e "${BLUE}3. 테스트 완료${NC}"
echo "============="

echo -e "${GREEN}🎉 인증 기능 테스트 완료!${NC}"
echo ""
echo -e "${BLUE}사용법:${NC}"
echo "1. 인증 비활성화: COMIX_ENABLE_AUTH=false"
echo "2. 인증 활성화: COMIX_ENABLE_AUTH=true + USERNAME/PASSWORD 설정"
echo "3. AirComix 앱에서 동일한 사용자명/패스워드로 로그인"