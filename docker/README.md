# Comix Server Docker 배포 가이드

AirComix iOS 앱과 호환되는 만화책 스트리밍 서버의 Docker 배포 가이드입니다.

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/comix-server/comix-server-python.git
cd comix-server-python
```

### 2. 환경 설정
```bash
# 환경 파일 생성
cp docker/.env.example docker/.env

# 만화 디렉토리 설정 (필수!)
vim docker/.env  # MANGA_DIRECTORY를 실제 경로로 수정
```

### 3. 서버 시작
```bash
# 자동 설정 및 시작
make quick-start

# 또는 단계별 실행
make setup
make run
```

### 4. 접속 확인
- 웹 브라우저에서 `http://localhost:31257` 접속
- AirComix iOS 앱에서 서버 주소 설정

## 📋 주요 명령어

### 기본 운영
```bash
make help          # 모든 명령어 확인
make run           # 서버 시작
make stop          # 서버 중지
make restart       # 서버 재시작
make logs          # 로그 확인
make status        # 상태 확인
```

### 개발 환경
```bash
make run-dev       # 개발 서버 시작 (핫 리로드)
make logs-dev      # 개발 서버 로그
make test          # 테스트 실행
make shell-dev     # 개발 컨테이너 셸 접속
```

### 유지보수
```bash
make clean         # 불필요한 Docker 리소스 정리
make update        # 최신 코드로 업데이트
make health        # 서버 상태 확인
```

## ⚙️ 환경 설정

### 필수 설정
```bash
# docker/.env 파일에서 설정
MANGA_DIRECTORY=/path/to/your/manga  # 만화 디렉토리 (절대 경로)
```

### 선택적 설정
```bash
COMIX_SERVER_PORT=31257              # 서버 포트
DEBUG_MODE=false                     # 디버그 모드
LOG_LEVEL=INFO                       # 로그 레벨
HIDDEN_FILES=.DS_Store,Thumbs.db     # 숨김 파일
```

## 📁 디렉토리 구조

```
docker/
├── Dockerfile              # 프로덕션 이미지
├── Dockerfile.dev          # 개발 이미지
├── docker-compose.yml      # 프로덕션 구성
├── docker-compose.dev.yml  # 개발 구성
├── .env.example            # 환경 변수 템플릿
├── .dockerignore           # Docker 빌드 제외 파일
└── README.md               # 이 파일
```

## 🔧 고급 설정

### 리소스 제한
```bash
# docker/.env에서 설정
MEMORY_LIMIT=1G              # 메모리 제한
CPU_LIMIT=2.0                # CPU 제한
MEMORY_RESERVATION=512M      # 메모리 예약
CPU_RESERVATION=1.0          # CPU 예약
```

### 로깅 설정
```bash
LOG_MAX_SIZE=10m             # 로그 파일 최대 크기
LOG_MAX_FILES=5              # 로그 파일 최대 개수
```

### 성능 튜닝
```bash
MAX_IMAGE_SIZE=10485760      # 최대 이미지 크기 (10MB)
CACHE_SIZE=100               # 캐시 크기
```

## 🐛 문제 해결

### 일반적인 문제

1. **만화 디렉토리 접근 불가**
   ```bash
   # 권한 확인
   ls -la /path/to/your/manga
   
   # Docker 컨테이너에서 확인
   make shell
   ls -la /manga
   ```

2. **포트 충돌**
   ```bash
   # 다른 포트 사용
   echo "COMIX_SERVER_PORT=31258" >> docker/.env
   make restart
   ```

3. **메모리 부족**
   ```bash
   # 리소스 제한 조정
   echo "MEMORY_LIMIT=2G" >> docker/.env
   make restart
   ```

### 로그 확인
```bash
# 실시간 로그
make logs

# 특정 서비스 로그
docker-compose -f docker/docker-compose.yml logs comix-server

# 에러 로그만
make logs | grep ERROR
```

### 컨테이너 디버깅
```bash
# 컨테이너 내부 접속
make shell

# 프로세스 확인
docker exec comix-server ps aux

# 네트워크 확인
docker exec comix-server netstat -tlnp
```

## 🔒 보안 고려사항

### 기본 보안 설정
- 비루트 사용자로 실행
- 읽기 전용 만화 디렉토리 마운트
- 불필요한 권한 제거 (`no-new-privileges`)
- 네트워크 격리

### 추가 보안 강화
```bash
# 방화벽 설정 (예: UFW)
sudo ufw allow 31257/tcp

# SSL/TLS 설정 (리버스 프록시 사용 권장)
# nginx, traefik 등을 통한 HTTPS 설정
```

## 📊 모니터링

### 기본 모니터링
```bash
# 시스템 리소스 사용량
docker stats comix-server

# 헬스체크
make health

# 서비스 상태
make status
```

### 고급 모니터링
- Prometheus + Grafana 연동
- 로그 수집 (ELK Stack)
- 알림 설정 (Alertmanager)

## 🚀 프로덕션 배포

### 권장 구성
1. **리버스 프록시** (nginx, traefik)
2. **SSL/TLS 인증서** (Let's Encrypt)
3. **로그 로테이션**
4. **백업 전략**
5. **모니터링 시스템**

### 예제 nginx 설정
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:31257;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 지원

- **이슈 리포트**: [GitHub Issues](https://github.com/comix-server/comix-server-python/issues)
- **문서**: [프로젝트 문서](../docs/)
- **커뮤니티**: [Discussions](https://github.com/comix-server/comix-server-python/discussions)

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](../LICENSE) 파일을 참조하세요.