# Comix Server 예제 및 튜토리얼

이 디렉토리에는 Comix Server를 다양한 환경에서 사용하는 예제들이 포함되어 있습니다.

## 📁 디렉토리 구조

```
examples/
├── README.md                    # 이 파일
├── basic-setup/                 # 기본 설정 예제
├── docker-examples/             # Docker 사용 예제
├── production-deployment/       # 프로덕션 배포 예제
├── client-integration/          # 클라이언트 통합 예제
├── custom-configurations/       # 커스텀 설정 예제
└── migration-guides/           # 마이그레이션 가이드
```

## 🚀 빠른 시작 예제

### 1. 기본 로컬 설정

가장 간단한 로컬 개발 환경 설정입니다.

```bash
# 저장소 클론
git clone https://github.com/comix-server/comix-server-python.git
cd comix-server-python

# 예제 설정 복사
cp examples/basic-setup/.env.example .env

# 만화 디렉토리 설정 (예제 데이터 사용)
mkdir -p ~/manga
cp -r examples/basic-setup/sample-manga/* ~/manga/

# 서버 실행
python -m venv .venv
source .venv/bin/activate
pip install -e .
comix-server
```

### 2. Docker 빠른 시작

Docker를 사용한 가장 빠른 설정 방법입니다.

```bash
# Docker Compose 설정 복사
cp examples/docker-examples/docker-compose.simple.yml docker-compose.yml
cp examples/docker-examples/.env.docker .env

# 만화 디렉토리 설정
mkdir -p ~/manga
# 여기에 만화 파일들을 복사

# 서비스 시작
docker-compose up -d
```

## 📚 상세 예제

각 예제는 독립적으로 실행 가능하며, 특정 사용 사례에 맞춰 설계되었습니다.

### [기본 설정](basic-setup/)
- 로컬 개발 환경 설정
- 환경 변수 설정 예제
- 샘플 만화 데이터

### [Docker 예제](docker-examples/)
- 단순 Docker 실행
- Docker Compose 설정
- 개발/프로덕션 환경 분리

### [프로덕션 배포](production-deployment/)
- Nginx + Gunicorn 설정
- Systemd 서비스 설정
- SSL/TLS 설정
- 모니터링 설정

### [클라이언트 통합](client-integration/)
- Python 클라이언트 예제
- JavaScript/Node.js 클라이언트
- AirComix 앱 연동 가이드

### [커스텀 설정](custom-configurations/)
- 다국어 환경 설정
- 대용량 컬렉션 최적화
- 보안 강화 설정

### [마이그레이션 가이드](migration-guides/)
- PHP comix-server에서 마이그레이션
- 다른 만화 서버에서 마이그레이션
- 데이터 변환 도구

## 🎯 사용 사례별 가이드

### 개인 사용자
```bash
# 홈 서버에서 개인 만화 컬렉션 서빙
cd examples/basic-setup/
./setup-personal.sh
```

### 소규모 팀
```bash
# 팀 내부 만화 서버 구축
cd examples/production-deployment/small-team/
./deploy.sh
```

### 대규모 서비스
```bash
# 고가용성 프로덕션 환경
cd examples/production-deployment/enterprise/
./deploy-ha.sh
```

## 🔧 개발자 가이드

### API 클라이언트 개발

```python
# Python 클라이언트 예제
from examples.client_integration.python_client import ComixClient

client = ComixClient("http://localhost:31257")
series_list = client.get_series_list()
```

### 커스텀 미들웨어

```python
# FastAPI 미들웨어 추가 예제
from examples.custom_configurations.middleware import CustomAuthMiddleware

app.add_middleware(CustomAuthMiddleware)
```

## 📖 튜토리얼

### 1. 첫 번째 서버 설정
- [기본 설정 튜토리얼](tutorials/01-basic-setup.md)
- [Docker로 시작하기](tutorials/02-docker-setup.md)

### 2. 고급 설정
- [성능 최적화](tutorials/03-performance-tuning.md)
- [보안 설정](tutorials/04-security-hardening.md)

### 3. 운영 및 모니터링
- [로그 관리](tutorials/05-logging-monitoring.md)
- [백업 및 복구](tutorials/06-backup-recovery.md)

## 🤝 기여하기

새로운 예제나 튜토리얼을 추가하고 싶다면:

1. 이 저장소를 포크합니다
2. `examples/` 디렉토리에 새 예제를 추가합니다
3. README.md를 업데이트합니다
4. Pull Request를 생성합니다

### 예제 작성 가이드라인

- 각 예제는 독립적으로 실행 가능해야 합니다
- 명확한 README.md를 포함해야 합니다
- 실제 사용 사례를 기반으로 해야 합니다
- 코드에 충분한 주석을 포함해야 합니다

## 📞 도움이 필요하신가요?

- 📖 [전체 문서](../docs/)
- 🐛 [이슈 리포트](https://github.com/comix-server/comix-server-python/issues)
- 💬 [토론](https://github.com/comix-server/comix-server-python/discussions)
- 📧 [이메일 지원](mailto:support@comix-server.com)