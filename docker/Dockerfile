# Comix Server Python Port - Production Docker Image
# Multi-stage build for optimized production deployment

# Build stage - 의존성 설치 및 빌드
FROM python:3.11-slim as builder

# 빌드 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# 시스템 의존성 설치 (빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 가상환경 생성 및 활성화
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 먼저 의존성 파일만 복사하여 레이어 캐싱 최적화
COPY pyproject.toml ./

# 기본 의존성만 먼저 설치 (소스 코드 변경 시 캐시 활용)
RUN pip install --upgrade pip setuptools wheel

# 소스 코드 복사
COPY app/ ./app/
COPY README.md ./

# 패키지 설치 및 캐시 정리
RUN pip install . && \
    rm -rf ~/.cache/pip /tmp/pip-* || true

# Production stage - 실행 환경
FROM python:3.11-slim as production

# 메타데이터 라벨
LABEL maintainer="Comix Server Team" \
      version="1.0.0" \
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
COPY --chown=comix:comix README.md ./

# 디버깅: 복사된 파일 구조 확인
RUN echo "=== App directory structure ===" && \
    find ./app -type f -name "*.py" | head -20 && \
    echo "=== Middleware files ===" && \
    ls -la ./app/middleware/ || echo "No middleware directory"

# 만화 디렉토리 생성 및 권한 설정
RUN mkdir -p /comix && \
    chown comix:comix /comix

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