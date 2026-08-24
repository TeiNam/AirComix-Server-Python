# Comix Server Python Port - Production Docker Image
# Multi-stage build for optimized production deployment

# Build stage - 의존성 설치 및 빌드
FROM python:3.11-slim AS builder

# uv 는 버전을 고정해야 빌드가 재현된다
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv

# 빌드 환경 변수 설정
# UV_PROJECT_ENVIRONMENT: production 스테이지가 통째로 복사할 venv 경로
# UV_LINK_MODE=copy: 스테이지 간 복사를 위해 하드링크 대신 실제 복사
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

# 시스템 의존성 설치 (빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# 의존성만 먼저 설치한다.
# 소스 코드가 바뀌어도 pyproject.toml/uv.lock 이 그대로면 이 레이어는 재사용된다.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-editable

# 소스 코드 복사 후 프로젝트 자체만 설치
COPY app/ ./app/
COPY images/ ./images/
COPY README.md ./
RUN uv sync --locked --no-editable

# Production stage - 실행 환경
FROM python:3.11-slim AS production

# 메타데이터 라벨
LABEL maintainer="Comix Server Team" \
      version="1.0.2" \
      description="Comic book streaming server compatible with AirComix iOS app" \
      org.opencontainers.image.source="https://github.com/comix-server/comix-server-python"

# 런타임 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    COMIX_MANGA_DIRECTORY=/comix \
    COMIX_SERVER_HOST=0.0.0.0 \
    COMIX_SERVER_PORT=31257

# 런타임 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    unrar-free \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 빌드 스테이지에서 가상환경 복사
COPY --from=builder /opt/venv /opt/venv

# 보안을 위한 비루트 사용자 생성
RUN groupadd -r -g 1000 comix && \
    useradd -r -u 1000 -g comix -d /app -s /bin/bash comix

# 애플리케이션 디렉토리 생성
WORKDIR /app

# 애플리케이션 코드 복사
COPY --chown=comix:comix app/ ./app/
COPY --chown=comix:comix images/ ./images/
COPY --chown=comix:comix README.md ./

# 만화 디렉토리 생성 및 권한 설정
# 만화 디렉토리는 읽기 전용으로 마운트되므로 썸네일 캐시는 별도 경로에 둔다.
RUN mkdir -p /comix /app/cache && \
    chown comix:comix /comix /app/cache

# 썸네일 캐시 경로 기본값 (읽기 전용 manga 마운트에서도 캐시가 동작하도록)
ENV COMIX_THUMBNAIL_CACHE_DIRECTORY=/app/cache

# 비루트 사용자로 전환
USER comix

# 포트 노출
EXPOSE 31257

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:31257/health || exit 1

# Python 경로 설정
ENV PYTHONPATH=/app

# 기본 실행 명령어
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "31257"]
