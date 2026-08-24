# 개발 가이드

## 로컬 개발 환경 설정

### 1. uv 설치

의존성은 `uv.lock` 으로 고정되어 있다. 재현 가능한 환경을 위해 [uv](https://docs.astral.sh/uv/) 를 사용한다.

```bash
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Homebrew:
brew install uv
```

### 2. 의존성 설치

```bash
# 락파일 기준으로 가상환경(.venv) 생성 및 개발 의존성 설치
uv sync --locked --extra dev
```

명령 실행은 `uv run` 을 앞에 붙이면 되고, 별도의 가상환경 활성화가 필요 없다.
`uv run` 은 환경을 자동으로 재동기화하므로 개발 의존성이 필요한 명령에는
`--extra dev` 를 함께 넘긴다.

```bash
uv run --extra dev pytest -q
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

### 4. 테스트 실행 (선택사항)

```bash
# 간단한 테스트 실행
python -m pytest tests/test_simple.py -v

# 모든 테스트 실행 (시간이 오래 걸릴 수 있음)
python -m pytest tests/ -v

# 커버리지와 함께 테스트
python -m pytest tests/ -v --cov=app --cov-report=html

# Docker 빌드 테스트 (권장)
make test-build
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
**해결**: `uv sync --locked --extra dev` 로 환경을 다시 동기화한 뒤 `uv run` 으로 실행

**문제**: `pytest: command not found`
**해결**: `uv sync --locked --extra dev` 실행 후 `uv run --extra dev pytest` 사용

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
# 1. 의존성 동기화
uv sync --locked --extra dev

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
## 릴리스

버전의 단일 출처는 `pyproject.toml` 이다. `app.__version__` 은 설치된 패키지
메타데이터에서 읽고, 이미지 라벨은 CI 가 빌드 시점에 찍는다. 버전 문자열을
손으로 고칠 곳은 없다.

```bash
make version       # 현재 버전 확인
make bump-patch    # +0.0.1  (1.0.2 → 1.0.3)  버그 수정
make bump-minor    # +0.1.0  (1.0.2 → 1.1.0)  기능 추가
make bump-major    # +1.0.0  (1.0.2 → 2.0.0)  호환성 깨짐
```

증가 명령은 `pyproject.toml` 과 `uv.lock` 을 함께 갱신한다. 이후 절차:

```bash
git switch -c release/v1.0.3
make bump-patch
git commit -am "chore: 버전 1.0.3"
git push -u origin release/v1.0.3
gh pr create --fill && gh pr merge --squash --delete-branch

git switch main && git pull
gh release create v1.0.3 --target main --notes "..."
```

릴리스를 발행하면 `release.yml` 이 Docker Hub 와 ghcr 양쪽에 `latest`,
`1.0.3`, `1.0`, `1` 을 푸시한다.

> **주의**: `docker-build.yml` 은 main 에 푸시할 때마다 `latest` 를
> `vX.Y.Z-preview` 빌드로 덮는다. 릴리스 이후 main 에 머지가 들어가면
> `latest` 는 다시 preview 를 가리킨다.
