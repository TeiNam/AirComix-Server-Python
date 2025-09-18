# Comix Server Python Port

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![AirComix Compatible](https://img.shields.io/badge/AirComix-100%25%20Compatible-blue?style=for-the-badge)](https://apps.apple.com/app/aircomix/)

AirComix iOS 앱과 100% 호환되는 만화책 스트리밍 서버의 Python 포트입니다. 기존 PHP 서버를 FastAPI로 재구현하여 더 나은 성능과 안정성을 제공합니다.

## ✨ 주요 개선사항

- 🚀 **성능 향상**: FastAPI 비동기 처리로 더 빠른 응답
- 🔒 **보안 강화**: 경로 순회 공격 방지, 입력 검증 개선
- 📦 **현대적 배포**: Docker 지원, 자동화된 설정
- 🧪 **안정성**: 195개 테스트로 검증된 품질
- 🌏 **인코딩**: 한글, 일본어 파일명 완벽 지원

## 🚀 빠른 시작

### Docker 사용 (권장)

```bash
# 저장소 클론
git clone https://github.com/comix-server/comix-server-python.git
cd comix-server-python

# Docker 디렉토리로 이동
cd docker

# 환경 설정
cp .env.example .env
# .env 파일에서 MANGA_DIRECTORY 경로 설정

# 실행
docker-compose up -d
```

### 로컬 설치

```bash
# Python 3.11+ 필요
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 설치
pip install -e .

# 환경 설정
cp .env.example .env
# .env 파일에서 COMIX_MANGA_DIRECTORY 설정

# 실행
comix-server
```

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
| `/manga/{path}` | 파일/디렉토리 목록 또는 이미지 스트리밍 |

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

- 🐛 버그 리포트: [GitHub Issues](https://github.com/comix-server/comix-server-python/issues)
- 💡 기능 요청: [GitHub Discussions](https://github.com/comix-server/comix-server-python/discussions)