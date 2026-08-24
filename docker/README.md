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
      - "31257:31257"
    volumes:
      - /path/to/your/manga:/comix:ro
      # 썸네일 캐시 (없으면 컨테이너를 다시 만들 때마다 재생성된다)
      - aircomix-cache:/app/cache
    environment:
      - COMIX_MANGA_DIRECTORY=/comix
    restart: unless-stopped

volumes:
  aircomix-cache:
EOF

# 서버 시작
docker-compose up -d
```

### Docker Run 사용

```bash
docker volume create aircomix-cache

docker run -d \
  --name aircomix-server \
  -p 31257:31257 \
  -v /path/to/your/manga:/comix:ro \
  -v aircomix-cache:/app/cache \
  -e COMIX_MANGA_DIRECTORY=/comix \
  --restart unless-stopped \
  aircomix/aircomix-server:latest
```

> 썸네일 캐시 기본 경로는 이미지에 `/app/cache` 로 설정되어 있습니다.
> 만화 디렉토리를 쓰기 가능하게 마운트하고 예전처럼 그 안에 캐시를 두려면
> `-e COMIX_THUMBNAIL_CACHE_DIRECTORY=/comix/.thumbnails` 를 지정하세요.

## 📋 환경 변수

모든 서버 설정은 `COMIX_` 접두어가 필요합니다. 접두어가 없는 이름은 무시됩니다.

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `COMIX_MANGA_DIRECTORY` | `~/comix` | 만화 파일이 있는 디렉토리 경로 (컨테이너에서는 `/comix`, 필수) |
| `COMIX_SERVER_PORT` | `31257` | 서버 포트 |
| `COMIX_DEBUG_MODE` | `false` | 디버그 모드 활성화 (API 문서 노출) |
| `COMIX_LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `COMIX_HIDDEN_FILES` | `[".", "..", "@eaDir", "Thumbs.db", ".DS_Store", ".thumbnails"]` | 숨김 파일 목록 (**JSON 배열**) |
| `COMIX_HIDDEN_PATTERNS` | `["__MACOSX"]` | 숨김 파일 패턴 (**JSON 배열**) |
| `COMIX_IMAGE_EXTENSIONS` | `["jpg", "jpeg", "gif", "png", "tif", "tiff", "bmp"]` | 이미지 확장자 (**JSON 배열**) |
| `COMIX_ARCHIVE_EXTENSIONS` | `["zip", "cbz", "rar", "cbr"]` | 아카이브 확장자 (**JSON 배열**) |
| `COMIX_MAX_FILE_SIZE` | `104857600` | 스트리밍 최대 파일 크기 (바이트, 최대 1GB) |
| `COMIX_CHUNK_SIZE` | `8192` | 스트리밍 청크 크기 (바이트) |
| `COMIX_ENABLE_AUTH` | `false` | 기본 인증 활성화 |
| `COMIX_AUTH_PASSWORD` | - | 인증 패스워드 (인증 활성화 시 필수, 최소 6자) |

> 목록형 설정(`*_FILES`, `*_PATTERNS`, `*_EXTENSIONS`)은 **JSON 배열 문자열**로 넘겨야 합니다.
> `jpg,jpeg,png` 처럼 콤마로 구분하면 설정 파싱이 실패하고 서버가 기동하지 않습니다.

## 🔐 인증 설정 (선택사항)

.htaccess 방식의 패스워드 인증을 사용할 수 있습니다:

```bash
docker run -d \
  --name aircomix-server \
  -p 31257:31257 \
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

- `GET /` - 만화 루트 디렉토리 이름 (AirComix 앱이 가장 먼저 호출)
- `GET /welcome.102` - 서버 기능 정보
- `GET /comix/{path}` - 디렉토리 목록 / 아카이브 목록 / 이미지 스트리밍 (요청 경로에 따라 분기)
- `GET /thumbnail/{path}` - 썸네일 생성
- `GET /{name}.thm` - 최상위 항목 썸네일 (AirComix 앱 호환)
- `GET /health` - 헬스체크 (인증 제외)
- `GET|POST|DELETE /admin/thumbnail/*` - 썸네일 캐시 관리 (`COMIX_ENABLE_AUTH=true` 일 때만 등록)

## 🔧 고급 설정

### 리소스 제한이 있는 Docker Compose

```yaml
version: '3.8'
services:
  aircomix:
    image: aircomix/aircomix-server:latest
    ports:
      - "31257:31257"
    volumes:
      - /path/to/your/manga:/comix:ro
      - aircomix-cache:/app/cache
    environment:
      - COMIX_MANGA_DIRECTORY=/comix
      - COMIX_LOG_LEVEL=INFO
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
      test: ["CMD", "curl", "-f", "http://localhost:31257/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  aircomix-cache:
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
   - 다른 포트 사용: `-p 31258:31257`

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