#!/bin/bash
# Comix Server 기본 설정 자동화 스크립트

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Comix Server 기본 설정 시작${NC}"
echo "=================================="

# 1. Python 버전 확인
echo -e "\n${BLUE}1. Python 버전 확인${NC}"
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$PYTHON_VERSION" == "3.11" || "$PYTHON_VERSION" == "3.12" ]]; then
        PYTHON_CMD="python3"
    else
        echo -e "${RED}Python 3.11 이상이 필요합니다. 현재 버전: $PYTHON_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}Python이 설치되지 않았습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 확인됨: $($PYTHON_CMD --version)${NC}"

# 2. 가상환경 생성
echo -e "\n${BLUE}2. 가상환경 설정${NC}"
if [[ ! -d ".venv" ]]; then
    echo "가상환경 생성 중..."
    $PYTHON_CMD -m venv .venv
    echo -e "${GREEN}✓ 가상환경 생성 완료${NC}"
else
    echo -e "${YELLOW}가상환경이 이미 존재합니다${NC}"
fi

# 가상환경 활성화
source .venv/bin/activate
echo -e "${GREEN}✓ 가상환경 활성화됨${NC}"

# 3. 의존성 설치
echo -e "\n${BLUE}3. 의존성 설치${NC}"
pip install --upgrade pip
pip install -e .
echo -e "${GREEN}✓ 의존성 설치 완료${NC}"

# 4. 설정 파일 생성
echo -e "\n${BLUE}4. 설정 파일 생성${NC}"
if [[ ! -f ".env" ]]; then
    cp examples/basic-setup/.env.example .env
    echo -e "${GREEN}✓ .env 파일 생성됨${NC}"
    
    # 사용자 홈 디렉토리로 기본 경로 설정
    MANGA_DIR="$HOME/manga"
    sed -i.bak "s|COMIX_MANGA_DIRECTORY=.*|COMIX_MANGA_DIRECTORY=$MANGA_DIR|" .env
    echo -e "${YELLOW}만화 디렉토리가 $MANGA_DIR로 설정되었습니다${NC}"
else
    echo -e "${YELLOW}.env 파일이 이미 존재합니다${NC}"
fi

# 5. 만화 디렉토리 생성
echo -e "\n${BLUE}5. 만화 디렉토리 설정${NC}"
MANGA_DIR=$(grep COMIX_MANGA_DIRECTORY .env | cut -d'=' -f2)
if [[ ! -d "$MANGA_DIR" ]]; then
    mkdir -p "$MANGA_DIR"
    echo -e "${GREEN}✓ 만화 디렉토리 생성됨: $MANGA_DIR${NC}"
else
    echo -e "${YELLOW}만화 디렉토리가 이미 존재합니다: $MANGA_DIR${NC}"
fi

# 6. 샘플 데이터 복사 (선택사항)
echo -e "\n${BLUE}6. 샘플 데이터 설정${NC}"
if [[ -d "examples/basic-setup/sample-manga" ]]; then
    read -p "샘플 만화 데이터를 복사하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp -r examples/basic-setup/sample-manga/* "$MANGA_DIR/"
        echo -e "${GREEN}✓ 샘플 데이터 복사 완료${NC}"
    else
        echo -e "${YELLOW}샘플 데이터를 건너뛰었습니다${NC}"
        echo -e "${YELLOW}$MANGA_DIR에 만화 파일을 직접 복사해주세요${NC}"
    fi
else
    echo -e "${YELLOW}샘플 데이터를 찾을 수 없습니다${NC}"
fi

# 7. 설정 테스트
echo -e "\n${BLUE}7. 설정 테스트${NC}"
if python -c "from app.models.config import settings; print(f'설정 로드 성공: {settings.manga_directory}')" 2>/dev/null; then
    echo -e "${GREEN}✓ 설정 파일 유효성 검사 통과${NC}"
else
    echo -e "${RED}✗ 설정 파일에 오류가 있습니다${NC}"
    exit 1
fi

# 8. 완료 메시지
echo -e "\n${GREEN}🎉 Comix Server 기본 설정 완료!${NC}"
echo "=================================="
echo -e "${BLUE}다음 단계:${NC}"
echo "1. 서버 시작: ${YELLOW}comix-server${NC}"
echo "2. 브라우저에서 접속: ${YELLOW}http://localhost:31257${NC}"
echo "3. 헬스 체크: ${YELLOW}curl http://localhost:31257/health${NC}"
echo ""
echo -e "${BLUE}만화 디렉토리:${NC} $MANGA_DIR"
echo -e "${BLUE}설정 파일:${NC} .env"
echo ""
echo -e "${YELLOW}AirComix 앱에서 연결하려면:${NC}"
echo "- 서버 주소: http://$(hostname -I | awk '{print $1}'):31257"
echo "- 또는: http://localhost:31257 (로컬 테스트용)"
echo ""
echo -e "${BLUE}문제가 발생하면:${NC}"
echo "- 로그 확인: ${YELLOW}COMIX_DEBUG_MODE=true comix-server${NC}"
echo "- 문서 참조: ${YELLOW}docs/TROUBLESHOOTING.md${NC}"