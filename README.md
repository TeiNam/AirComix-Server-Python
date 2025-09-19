# Comix Server Python Port

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![AirComix Compatible](https://img.shields.io/badge/AirComix-100%25%20Compatible-blue?style=for-the-badge)](https://apps.apple.com/app/aircomix/)

AirComix iOS 앱과 100% 호환되는 만화책 스트리밍 서버의 Python 포트입니다. 기존 PHP 서버를 FastAPI로 재구현하여 더 나은 성능과 안정성을 제공합니다.

## Docker Repository
- https://hub.docker.com/r/teinam/aircomix-server 


## ✨ 주요 개선사항

- 🚀 **성능 향상**: FastAPI 비동기 처리로 더 빠른 응답
- 🔒 **보안 강화**: 경로 순회 공격 방지, 입력 검증 개선
- 📦 **현대적 배포**: Docker 지원, 자동화된 설정
- 🧪 **안정성**: 195개 테스트로 검증된 품질
- 🌏 **인코딩**: 한글, 일본어 파일명 완벽 지원

## 🚀 빠른 시작

### Docker Hub에서 바로 사용

```bash
# Docker Hub에서 최신 이미지 가져오기
docker pull [사용자명]/aircomix-server:latest

# 간단한 실행 (만화 디렉토리를 /path/to/your/comix로 변경)
docker run -d \
  --name aircomix-server \
  -p 31257:31257 \
  -v /path/to/your/comix:/comix:ro \
  [사용자명]/aircomix-server:latest
```

### 소스에서 빌드 (권장)

```bash
# 저장소 클론
git clone https://github.com/[사용자명]/comix-server-python.git
cd comix-server-python

# 빠른 시작 (자동 설정 및 실행)
make quick-start

# 실행
docker-compose up -d
```

### 로컬 설치

```bash
# Python 3.11+ 필요
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 개발 의존성 포함 설치
pip install -e ".[dev]"

# 테스트용 만화 디렉토리 생성
mkdir -p /tmp/test-comix
export COMIX_MANGA_DIRECTORY=/tmp/test-comix

# 실행
python -m app.main
```

> 📖 **자세한 개발 가이드**: [DEVELOPMENT.md](DEVELOPMENT.md) 참조

## � 설정

주요 환경 변수:

```bash
COMIX_MANGA_DIRECTORY=/path/to/manga  # 만화 디렉토리
COMIX_SERVER_PORT=31257               # 서버 포트
COMIX_DEBUG_MODE=false                # 디버그 모드
COMIX_LOG_LEVEL=INFO                  # 로그 레벨
```

## 📱 AirComix 연결

1. AirComix iOS 앱 설치
2. 서버 설정에서 IP 주소와 포트(31257) 입력
3. 만화 컬렉션 탐색 및 읽기

서버 접속: `http://localhost:31257`

## 🐳 Docker 명령어

```bash
# Docker 디렉토리에서 실행
cd docker

# 서비스 시작
docker-compose up -d

# 개발 모드 (핫 리로드)
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down

# 상태 확인
docker-compose ps

# 이미지 빌드
docker-compose build
```

## 🌐 API 엔드포인트

| 엔드포인트 | 설명 |
|------------|------|
| `/` | 만화 디렉토리 이름 반환 |
| `/welcome.102` | 서버 기능 정보 |
| `/health` | 서버 상태 확인 |
| `/comix/{path}` | 파일/디렉토리 목록 또는 이미지 스트리밍 |

## 🐳 Docker 이미지

### 사용 가능한 태그

| 태그 | 설명 | 플랫폼 |
|------|------|--------|
| `latest` | 최신 안정 버전 | linux/amd64, linux/arm64 |
| `v1.0.0` | 특정 버전 (권장) | linux/amd64, linux/arm64 |
| `v1.0.0-preview` | 다음 버전 미리보기 | linux/amd64, linux/arm64 |
| `dev` | 개발 버전 | linux/amd64, linux/arm64 |

### Docker Hub
```bash
docker pull [사용자명]/aircomix-server:latest
docker pull [사용자명]/aircomix-server:dev
```

### GitHub Container Registry
```bash
docker pull ghcr.io/[사용자명]/aircomix-server:latest
docker pull ghcr.io/[사용자명]/aircomix-server:dev
```

### 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `COMIX_MANGA_DIRECTORY` | `/comix` | 만화 파일 디렉토리 |
| `COMIX_SERVER_PORT` | `31257` | 서버 포트 |
| `COMIX_DEBUG_MODE` | `false` | 디버그 모드 |
| `COMIX_LOG_LEVEL` | `INFO` | 로그 레벨 |
| `COMIX_ENABLE_AUTH` | `false` | 기본 인증 활성화 |
| `COMIX_AUTH_PASSWORD` | - | 인증 패스워드 (.htaccess 방식, 인증 활성화 시 필수) |

### 인증 설정

보안이 필요한 환경에서는 .htaccess 방식의 패스워드 인증을 활성화할 수 있습니다:

```bash
# 인증 활성화 (.htaccess 방식)
docker run -d \
  --name aircomix-server \
  -p 31257:31257 \
  -v /path/to/your/comix:/comix \
  -e COMIX_ENABLE_AUTH=true \
  -e COMIX_AUTH_PASSWORD=secure_password_123 \
  [사용자명]/aircomix-server:latest
```

**PHP 원본과 완전 호환**: .htaccess 방식으로 패스워드만 확인하며, AirComix 앱에서 투명하게 작동합니다.

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🤝 기여

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/name`)
3. 변경사항 커밋 (`git commit -m 'Add feature'`)
4. 브랜치 푸시 (`git push origin feature/name`)
5. Pull Request 생성

## � 지프로젝트 구조

```
comix-server-python/
├── app/                    # 메인 애플리케이션
├── docker/                 # Docker 설정 파일들
│   ├── Dockerfile         # 프로덕션 이미지
│   ├── Dockerfile.dev     # 개발 이미지
│   ├── docker-compose.yml # 프로덕션 설정
│   ├── docker-compose.dev.yml # 개발 설정
│   └── .env.example       # 환경 변수 예시
├── tests/                  # 테스트 파일들
├── scripts/               # 유틸리티 스크립트
└── docs/                  # 문서
```

## 📞 지원

- 🐛 버그 리포트: [GitHub Issues](https://github.com/TeiNam/AirComix-Server-Python/issues)
- 💡 기능 요청: [GitHub Discussions](https://github.com/TeiNam/AirComix-Server-Python/discussions)