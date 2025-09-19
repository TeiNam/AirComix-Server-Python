# GitHub Actions 설정 가이드

이 문서는 Comix Server의 CI/CD 파이프라인을 설정하는 방법을 설명합니다.

## 필요한 GitHub Secrets

GitHub 저장소의 Settings > Secrets and variables > Actions에서 다음 secrets을 설정해야 합니다:

### Docker Hub 배포용
- `DOCKER_USERNAME`: Docker Hub 사용자명
- `DOCKER_TOKEN`: Docker Hub 액세스 토큰

### Docker Hub 액세스 토큰 생성 방법
1. [Docker Hub](https://hub.docker.com)에 로그인
2. Account Settings > Security > New Access Token
3. 토큰 이름 입력 (예: "github-actions")
4. 권한: Read, Write, Delete 선택
5. 생성된 토큰을 `DOCKER_PASSWORD`에 설정

## CI/CD 워크플로우 설명

### 1. 테스트 워크플로우 (`test.yml`)
- **트리거**: main, develop 브랜치 push 및 main으로의 PR
- **기능**:
  - Python 3.11, 3.12에서 테스트 실행
  - 코드 커버리지 측정 및 Codecov 업로드
  - 코드 품질 검사 (Black, isort, flake8, mypy)

### 2. Docker 빌드 워크플로우 (`docker-build.yml`)
- **트리거**: main, develop 브랜치 push, 태그 push, PR
- **기능**:
  - 멀티 플랫폼 빌드 (linux/amd64, linux/arm64)
  - Docker Hub에 자동 배포
  - 브랜치별 태그 전략:
    - `main` → `latest` 태그
    - `develop` → `dev` 태그
    - `v1.2.3` → `1.2.3`, `1.2`, `1` 태그

### 3. 릴리스 워크플로우 (`release.yml`)
- **트리거**: GitHub Release 생성 시
- **기능**:
  - Docker Hub와 GitHub Container Registry에 동시 배포
  - 버전별 태그 생성
  - 릴리스 노트에 Docker 이미지 정보 추가

## 브랜치 전략

### main 브랜치
- 프로덕션 준비 코드
- `latest` 태그로 Docker 이미지 배포
- 모든 테스트 통과 필수

### develop 브랜치
- 개발 중인 코드
- `dev` 태그로 Docker 이미지 배포
- 새로운 기능 개발 및 테스트

### 릴리스 태그
- `v1.0.0` 형식의 태그
- 자동으로 여러 태그 생성 (`1.0.0`, `1.0`, `1`, `latest`)

## Docker 이미지 사용법

### Docker Hub에서 가져오기
```bash
# 최신 버전
docker pull [사용자명]/comix-server:latest

# 특정 버전
docker pull [사용자명]/comix-server:1.0.0

# 개발 버전
docker pull [사용자명]/comix-server:dev
```

### GitHub Container Registry에서 가져오기
```bash
# 최신 버전
docker pull ghcr.io/[사용자명]/comix-server:latest

# 특정 버전
docker pull ghcr.io/[사용자명]/comix-server:1.0.0
```

## 로컬 테스트

CI/CD 파이프라인을 로컬에서 테스트하려면:

```bash
# 테스트 실행
make test

# Docker 이미지 빌드
make build

# 코드 품질 검사
black --check app/ tests/
isort --check-only app/ tests/
flake8 app/ tests/
mypy app/
```

## 문제 해결

### 빌드 실패 시
1. 로컬에서 `make build` 실행하여 Docker 빌드 확인
2. 테스트 실패 시 `make test` 실행하여 로컬 테스트 확인
3. Secrets 설정 확인

### 배포 실패 시
1. Docker Hub 로그인 정보 확인
2. 저장소 권한 확인
3. 액세스 토큰 유효성 확인

## 보안 고려사항

- Docker Hub 비밀번호 대신 액세스 토큰 사용
- 최소 권한 원칙 적용
- 정기적인 토큰 갱신
- 민감한 정보는 GitHub Secrets 사용