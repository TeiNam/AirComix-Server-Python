# AirComix Server

AirComix iOS 앱과 100% 호환되는 만화책 스트리밍 서버입니다. CBZ, CBR, ZIP, RAR 형식의 만화 파일을 지원하며, 이미지 리사이징과 썸네일 생성 기능을 제공합니다.

## 🚀 빠른 시작

### Docker Compose 사용 (권장)

```bash
# docker-compose.yml 생성
cat > docker-compose.yml << EOF
version: '3.8'
services:
  aircomix:
    image: aircomix/aircomix-server:latest
    ports:
      - "31257:8000"
    volumes:
      - /path/to/your/manga:/comix
    environment:
      - MANGA_DIRECTORY=/comix
    restart: unless-stopped
EOF

# 서버 시작
docker-compose up -d
```

### Docker Run 사용

```bash
docker run -d \
  --name aircomix-server \
  -p 31257:8000 \
  -v /path/to/your/manga:/comix \
  -e MANGA_DIRECTORY=/comix \
  --restart unless-stopped \
  aircomix/aircomix-server:latest
```

## 📋 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `MANGA_DIRECTORY` | `/comix` | 만화 파일이 있는 디렉토리 경로 (필수) |
| `DEBUG_MODE` | `false` | 디버그 모드 활성화 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG, INFO, WARNING, ERROR) |
| `HIDDEN_FILES` | `.DS_Store,Thumbs.db` | 숨김 파일 목록 |
| `MAX_IMAGE_SIZE` | `10485760` | 최대 이미지 크기 (바이트) |

## 🔐 인증 설정 (선택사항)

.htaccess 방식의 패스워드 인증을 사용할 수 있습니다:

```bash
docker run -d \
  --name aircomix-server \
  -p 31257:8000 \
  -v /path/to/your/manga:/comix \
  -e COMIX_MANGA_DIRECTORY=/comix \
  -e COMIX_ENABLE_AUTH=true \
  -e COMIX_AUTH_PASSWORD=your_password \
  aircomix/aircomix-server:latest
```

## 📁 지원 파일 형식

### 압축 파일
- **CBZ** (Comic Book ZIP)
- **CBR** (Comic Book RAR)
- **ZIP** 아카이브
- **RAR** 아카이브

### 이미지 파일
- JPEG, PNG, GIF, BMP, WebP

## 🌐 API 엔드포인트

- `GET /` - 루트 디렉토리 브라우징
- `GET /browse/{path}` - 디렉토리 탐색
- `GET /image/{path}` - 이미지 스트리밍
- `GET /thumbnail/{path}` - 썸네일 생성
- `GET /info/{path}` - 파일 정보 조회
- `GET /health` - 헬스체크

## 🔧 고급 설정

### 리소스 제한이 있는 Docker Compose

```yaml
version: '3.8'
services:
  aircomix:
    image: aircomix/aircomix-server:latest
    ports:
      - "31257:8000"
    volumes:
      - /path/to/your/manga:/comix
    environment:
      - MANGA_DIRECTORY=/comix
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '1.0'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### nginx 리버스 프록시

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:31257;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 모니터링

### 헬스체크
```bash
curl http://localhost:31257/health
```

### 로그 확인
```bash
# Docker Compose
docker-compose logs -f aircomix

# Docker Run
docker logs -f aircomix-server
```

### 리소스 사용량
```bash
docker stats aircomix-server
```

## 🐛 문제 해결

### 일반적인 문제

1. **만화 디렉토리 접근 불가**
   - 볼륨 마운트 경로 확인: `-v /correct/path:/comix`
   - 디렉토리 권한 확인: `ls -la /path/to/your/manga`
   - **주의**: 읽기 전용(`:ro`) 마운트 시 구동 에러 발생 가능

2. **포트 충돌**
   - 다른 포트 사용: `-p 31258:8000`

3. **메모리 부족**
   - 메모리 제한 증가: `--memory=2g`

### 디버깅

```bash
# 컨테이너 내부 접속
docker exec -it aircomix-server /bin/bash

# 환경 변수 확인
docker exec aircomix-server env | grep MANGA

# 마운트된 디렉토리 확인
docker exec aircomix-server ls -la /comix

# 프로세스 확인
docker exec aircomix-server ps aux
```

## 🏷️ 태그

- `latest` - 최신 안정 버전
- `v1.x.x` - 특정 버전
- `dev` - 개발 버전 (불안정)

## 📞 지원

- **GitHub**: [aircomix/aircomix-server](https://github.com/aircomix/aircomix-server)
- **Issues**: [버그 리포트 및 기능 요청](https://github.com/aircomix/aircomix-server/issues)
- **Documentation**: [전체 문서](https://github.com/aircomix/aircomix-server/tree/main/docs)

## 📄 라이선스

MIT License