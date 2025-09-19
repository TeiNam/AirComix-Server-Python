# 개발 가이드

## 로컬 개발 환경 설정

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 2. 의존성 설치

```bash
# 개발 의존성 포함 설치
pip install -e ".[dev]"
```

### 3. 환경 변수 설정

```bash
# 테스트용 만화 디렉토리 생성
mkdir -p /tmp/test-comix
echo "test" > /tmp/test-comix/test.txt

# 환경 변수 설정
export COMIX_MANGA_DIRECTORY=/tmp/test-comix
export COMIX_DEBUG_MODE=true
```

### 4. 테스트 실행

```bash
# 모든 테스트 실행
python -m pytest tests/ -v

# 커버리지와 함께 테스트
python -m pytest tests/ -v --cov=app --cov-report=html

# 특정 테스트만 실행
python -m pytest tests/test_config.py -v
```

### 5. 코드 품질 검사

```bash
# Black 포매팅
black app/ tests/

# isort import 정렬
isort app/ tests/

# flake8 린팅
flake8 app/ tests/

# mypy 타입 체크
mypy app/
```

### 6. 서버 실행

```bash
# 개발 서버 실행
python -m app.main

# 또는 uvicorn 직접 사용
uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 31257
```

## Docker 개발 환경

### 1. Docker Compose 사용

```bash
# 개발 환경 시작
cd docker
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose -f docker-compose.dev.yml logs -f

# 컨테이너 셸 접속
docker exec -it comix-server-dev /bin/bash
```

### 2. Makefile 명령어

```bash
# 빠른 시작
make quick-start

# 개발 환경 시작
make run-dev

# 테스트 실행
make test

# Docker 빌드 테스트
make test-build

# 인증 기능 테스트
make test-auth
```

## 일반적인 문제 해결

### 가상환경 관련

**문제**: `ModuleNotFoundError: No module named 'app'`
**해결**: 가상환경이 활성화되어 있는지 확인하고 `pip install -e ".[dev]"` 실행

**문제**: `pytest: command not found`
**해결**: 가상환경 활성화 후 개발 의존성 설치

### 테스트 관련

**문제**: `ValueError: manga 디렉토리가 존재하지 않습니다`
**해결**: `COMIX_MANGA_DIRECTORY` 환경 변수 설정 및 디렉토리 생성

**문제**: 테스트 실행 시 권한 오류
**해결**: 테스트 디렉토리 권한 확인 (`chmod 755 /tmp/test-comix`)

### Docker 관련

**문제**: Docker 빌드 실패
**해결**: `make test-build` 실행하여 로컬에서 먼저 테스트

**문제**: 포트 충돌
**해결**: `.env` 파일에서 `COMIX_SERVER_PORT` 변경

## 개발 워크플로우

### 1. 새 기능 개발

```bash
# 1. 가상환경 활성화
source .venv/bin/activate

# 2. 브랜치 생성
git checkout -b feature/new-feature

# 3. 코드 작성
# ...

# 4. 테스트 실행
python -m pytest tests/ -v

# 5. 코드 품질 검사
black app/ tests/
isort app/ tests/
flake8 app/ tests/

# 6. 커밋 및 푸시
git add .
git commit -m "feat: 새 기능 추가"
git push origin feature/new-feature
```

### 2. 버그 수정

```bash
# 1. 문제 재현 테스트 작성
# tests/test_bug_fix.py

# 2. 테스트 실행 (실패 확인)
python -m pytest tests/test_bug_fix.py -v

# 3. 버그 수정
# app/...

# 4. 테스트 실행 (성공 확인)
python -m pytest tests/test_bug_fix.py -v

# 5. 전체 테스트 실행
python -m pytest tests/ -v
```

## 유용한 명령어

```bash
# 가상환경 상태 확인
which python
pip list

# 서버 상태 확인
curl http://localhost:31257/health

# Docker 컨테이너 상태 확인
docker ps | grep comix

# 로그 실시간 확인
tail -f logs/comix-server.log

# 테스트 커버리지 확인
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```