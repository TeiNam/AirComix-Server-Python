# 기본 설정 예제

가장 간단한 Comix Server 설정 방법을 보여주는 예제입니다.

## 📋 요구사항

- Python 3.11 이상
- 약 100MB 디스크 공간
- 만화 파일 (ZIP, CBZ, RAR, CBR 또는 이미지 파일)

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 디렉토리로 이동
cd comix-server-python

# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 의존성 설치
pip install -e .
```

### 2. 설정 파일 생성

```bash
# 예제 설정 파일 복사
cp examples/basic-setup/.env.example .env

# 설정 파일 편집
nano .env  # 또는 원하는 에디터 사용
```

### 3. 만화 디렉토리 준비

```bash
# 만화 디렉토리 생성
mkdir -p ~/manga

# 예제 데이터 복사 (선택사항)
cp -r examples/basic-setup/sample-manga/* ~/manga/

# 또는 본인의 만화 파일을 복사
# cp -r /path/to/your/manga/* ~/manga/
```

### 4. 서버 실행

```bash
# 서버 시작
comix-server

# 또는 Python 모듈로 실행
python -m app.main
```

### 5. 접속 확인

브라우저에서 `http://localhost:31257`로 접속하거나:

```bash
# 명령행에서 테스트
curl http://localhost:31257/
curl http://localhost:31257/health
curl http://localhost:31257/manga/
```

## 📁 파일 구조

```
examples/basic-setup/
├── README.md                 # 이 파일
├── .env.example             # 환경 변수 예제
├── setup.sh                 # 자동 설정 스크립트
├── sample-manga/            # 샘플 만화 데이터
│   ├── Series A/
│   │   ├── Volume 1.zip
│   │   └── cover.jpg
│   ├── Series B/
│   │   └── Chapter 01/
│   │       ├── page001.jpg
│   │       └── page002.jpg
│   └── standalone.cbz
└── test-client.py           # 테스트 클라이언트
```

## ⚙️ 설정 옵션

### 환경 변수 (.env 파일)

```bash
# 기본 서버 설정
COMIX_MANGA_DIRECTORY=/home/user/manga
COMIX_SERVER_HOST=0.0.0.0
COMIX_SERVER_PORT=31257

# 로깅 설정
COMIX_DEBUG_MODE=false
COMIX_LOG_LEVEL=INFO

# 파일 필터링 (선택사항)
COMIX_HIDDEN_FILES=.DS_Store,Thumbs.db,@eaDir
COMIX_HIDDEN_PATTERNS=__MACOSX,.git

# 지원 파일 형식 (선택사항)
COMIX_IMAGE_EXTENSIONS=jpg,jpeg,png,gif,bmp,tif,tiff
COMIX_ARCHIVE_EXTENSIONS=zip,cbz,rar,cbr
```

### 주요 설정 설명

| 설정 | 설명 | 예제 |
|------|------|------|
| `COMIX_MANGA_DIRECTORY` | 만화 파일이 저장된 디렉토리 | `/home/user/manga` |
| `COMIX_SERVER_PORT` | 서버 포트 번호 | `31257` |
| `COMIX_DEBUG_MODE` | 디버그 모드 (개발용) | `true` |
| `COMIX_LOG_LEVEL` | 로그 레벨 | `DEBUG`, `INFO`, `WARNING` |

## 🧪 테스트

### 자동 테스트 실행

```bash
# 설정 테스트
python examples/basic-setup/test-client.py

# 또는 수동 테스트
curl -s http://localhost:31257/health | grep "healthy"
```

### 수동 테스트

```bash
# 1. 서버 정보 확인
curl http://localhost:31257/

# 2. 헬스 체크
curl http://localhost:31257/health

# 3. 디렉토리 목록
curl http://localhost:31257/manga/

# 4. 특정 시리즈 목록
curl "http://localhost:31257/manga/Series%20A/"

# 5. 아카이브 내용
curl "http://localhost:31257/manga/Series%20A/Volume%201.zip"

# 6. 이미지 다운로드
curl "http://localhost:31257/manga/Series%20A/Volume%201.zip/page001.jpg" -o test-image.jpg
```

## 📱 AirComix 앱 연결

### iOS AirComix 앱 설정

1. **AirComix 앱 설치**
   - App Store에서 "AirComix" 검색 후 설치

2. **서버 추가**
   - 앱 실행 후 "서버 추가" 선택
   - 서버 주소: `http://your-ip:31257`
   - 이름: 원하는 서버 이름 입력

3. **연결 테스트**
   - "연결 테스트" 버튼 클릭
   - 성공 시 만화 목록이 표시됨

### 네트워크 설정

```bash
# 현재 IP 주소 확인
ip addr show  # Linux
ifconfig      # macOS
ipconfig      # Windows

# 방화벽 설정 (필요시)
sudo ufw allow 31257  # Ubuntu
```

## 🔧 문제 해결

### 일반적인 문제

#### 1. 서버가 시작되지 않음

```bash
# 포트 충돌 확인
sudo netstat -tlnp | grep 31257

# 다른 포트 사용
export COMIX_SERVER_PORT=8080
comix-server
```

#### 2. 만화 디렉토리 접근 불가

```bash
# 디렉토리 권한 확인
ls -la ~/manga

# 권한 수정
chmod 755 ~/manga
chmod 644 ~/manga/*
```

#### 3. 이미지가 표시되지 않음

```bash
# 파일 형식 확인
file ~/manga/image.jpg

# 지원 형식 확인
echo $COMIX_IMAGE_EXTENSIONS
```

### 로그 확인

```bash
# 디버그 모드로 실행
export COMIX_DEBUG_MODE=true
export COMIX_LOG_LEVEL=DEBUG
comix-server
```

## 📈 성능 최적화

### 기본 최적화

```bash
# 환경 변수 설정
export COMIX_LOG_LEVEL=WARNING  # 로그 레벨 낮춤
export COMIX_DEBUG_MODE=false   # 디버그 모드 비활성화
```

### 대용량 컬렉션

```bash
# 파일 캐시 설정 (향후 버전)
export COMIX_ENABLE_CACHE=true
export COMIX_CACHE_SIZE=1000
```

## 🔄 업그레이드

### 새 버전으로 업데이트

```bash
# Git으로 업데이트
git pull origin main

# 의존성 업데이트
pip install -e . --upgrade

# 서버 재시작
# Ctrl+C로 중지 후 다시 실행
comix-server
```

## 📚 다음 단계

기본 설정이 완료되었다면:

1. **[Docker 예제](../docker-examples/)** - 컨테이너화된 배포
2. **[프로덕션 배포](../production-deployment/)** - 실제 서비스 운영
3. **[커스텀 설정](../custom-configurations/)** - 고급 설정 옵션
4. **[클라이언트 통합](../client-integration/)** - 다양한 클라이언트 연동

## 💡 팁

- **성능**: SSD 사용 시 더 빠른 이미지 로딩
- **보안**: 외부 접근 시 방화벽 설정 필수
- **백업**: 설정 파일과 만화 컬렉션 정기 백업
- **모니터링**: 로그 파일 정기 확인

## 🤝 도움말

문제가 발생하면:

1. [문제 해결 가이드](../../docs/TROUBLESHOOTING.md) 확인
2. [GitHub Issues](https://github.com/comix-server/comix-server-python/issues)에서 검색
3. 새로운 이슈 생성 또는 토론 참여