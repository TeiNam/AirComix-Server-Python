# 설정 가이드

Comix Server의 모든 설정 옵션과 사용법을 설명합니다.

## 설정 방법

Comix Server는 다음 순서로 설정을 로드합니다:

1. **기본값** (코드에 정의된 값)
2. **환경 변수** (`COMIX_` 접두사)
3. **설정 파일** (`.env` 파일)
4. **명령행 인수** (일부 옵션만)

## 환경 변수

모든 환경 변수는 `COMIX_` 접두사를 사용합니다.

### 기본 서버 설정

#### `COMIX_MANGA_DIRECTORY`
- **기본값**: `/manga`
- **설명**: 만화 컬렉션이 저장된 디렉토리 경로
- **예제**: 
  ```bash
  export COMIX_MANGA_DIRECTORY="/home/user/manga"
  ```

#### `COMIX_SERVER_HOST`
- **기본값**: `0.0.0.0`
- **설명**: 서버가 바인드할 호스트 주소
- **옵션**: 
  - `0.0.0.0`: 모든 인터페이스
  - `127.0.0.1`: 로컬호스트만
  - 특정 IP 주소
- **예제**:
  ```bash
  export COMIX_SERVER_HOST="127.0.0.1"  # 로컬만
  export COMIX_SERVER_HOST="192.168.1.100"  # 특정 IP
  ```

#### `COMIX_SERVER_PORT`
- **기본값**: `31257`
- **설명**: 서버 포트 번호
- **범위**: 1024-65535
- **예제**:
  ```bash
  export COMIX_SERVER_PORT="8080"
  ```

### 로깅 설정

#### `COMIX_DEBUG_MODE`
- **기본값**: `false`
- **설명**: 디버그 모드 활성화
- **옵션**: `true`, `false`
- **효과**:
  - 상세한 로그 출력
  - 오류 시 스택 트레이스 표시
  - CORS 미들웨어 활성화
- **예제**:
  ```bash
  export COMIX_DEBUG_MODE="true"
  ```

#### `COMIX_LOG_LEVEL`
- **기본값**: `INFO`
- **설명**: 로그 레벨 설정
- **옵션**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **예제**:
  ```bash
  export COMIX_LOG_LEVEL="DEBUG"
  ```

### 파일 필터링 설정

#### `COMIX_HIDDEN_FILES`
- **기본값**: `".,..,.DS_Store,Thumbs.db,@eaDir"`
- **설명**: 숨길 파일명 목록 (쉼표 구분)
- **예제**:
  ```bash
  export COMIX_HIDDEN_FILES=".DS_Store,Thumbs.db,desktop.ini"
  ```

#### `COMIX_HIDDEN_PATTERNS`
- **기본값**: `"__MACOSX"`
- **설명**: 숨길 디렉토리 패턴 (쉼표 구분)
- **예제**:
  ```bash
  export COMIX_HIDDEN_PATTERNS="__MACOSX,.git,node_modules"
  ```

### 지원 파일 형식

#### `COMIX_IMAGE_EXTENSIONS`
- **기본값**: `"jpg,jpeg,gif,png,tif,tiff,bmp"`
- **설명**: 지원할 이미지 파일 확장자 (쉼표 구분)
- **예제**:
  ```bash
  export COMIX_IMAGE_EXTENSIONS="jpg,jpeg,png,gif,webp"
  ```

#### `COMIX_ARCHIVE_EXTENSIONS`
- **기본값**: `"zip,cbz,rar,cbr"`
- **설명**: 지원할 아카이브 파일 확장자 (쉼표 구분)
- **예제**:
  ```bash
  export COMIX_ARCHIVE_EXTENSIONS="zip,cbz,rar,cbr,7z"
  ```

## 설정 파일

### .env 파일

프로젝트 루트에 `.env` 파일을 생성하여 환경 변수를 설정할 수 있습니다.

```bash
# .env 파일 예제

# 기본 서버 설정
COMIX_MANGA_DIRECTORY=/home/user/manga
COMIX_SERVER_HOST=0.0.0.0
COMIX_SERVER_PORT=31257

# 로깅 설정
COMIX_DEBUG_MODE=false
COMIX_LOG_LEVEL=INFO

# 파일 필터링
COMIX_HIDDEN_FILES=.DS_Store,Thumbs.db,@eaDir
COMIX_HIDDEN_PATTERNS=__MACOSX,.git

# 지원 파일 형식
COMIX_IMAGE_EXTENSIONS=jpg,jpeg,png,gif,bmp,tif,tiff
COMIX_ARCHIVE_EXTENSIONS=zip,cbz,rar,cbr
```

### 설정 파일 우선순위

1. 명령행에서 지정한 `.env` 파일
2. 현재 디렉토리의 `.env` 파일
3. 환경 변수
4. 기본값

## 프로덕션 설정

### Gunicorn 설정

`gunicorn.conf.py` 파일에서 Gunicorn 관련 설정을 조정할 수 있습니다.

```python
# gunicorn.conf.py

import multiprocessing
import os

# 워커 설정
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# 네트워크 설정
bind = f"0.0.0.0:{os.getenv('COMIX_SERVER_PORT', '31257')}"
backlog = 2048

# 성능 설정
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120
keepalive = 2

# 로깅 설정
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('COMIX_LOG_LEVEL', 'info').lower()
```

### 환경별 설정 예제

#### 개발 환경

```bash
# .env.development
COMIX_MANGA_DIRECTORY=./test_sample_data
COMIX_SERVER_HOST=127.0.0.1
COMIX_SERVER_PORT=31257
COMIX_DEBUG_MODE=true
COMIX_LOG_LEVEL=DEBUG
```

#### 스테이징 환경

```bash
# .env.staging
COMIX_MANGA_DIRECTORY=/var/lib/comix/manga
COMIX_SERVER_HOST=0.0.0.0
COMIX_SERVER_PORT=31257
COMIX_DEBUG_MODE=false
COMIX_LOG_LEVEL=INFO
```

#### 프로덕션 환경

```bash
# .env.production
COMIX_MANGA_DIRECTORY=/var/lib/comix/manga
COMIX_SERVER_HOST=127.0.0.1
COMIX_SERVER_PORT=31257
COMIX_DEBUG_MODE=false
COMIX_LOG_LEVEL=WARNING

# 성능 최적화
GUNICORN_WORKERS=8
GUNICORN_WORKER_CONNECTIONS=1000
```

## Docker 설정

### Docker Compose 환경 변수

```yaml
# docker-compose.yml
version: '3.8'

services:
  comix-server:
    image: comix-server:latest
    environment:
      - COMIX_MANGA_DIRECTORY=/manga
      - COMIX_SERVER_HOST=0.0.0.0
      - COMIX_SERVER_PORT=31257
      - COMIX_DEBUG_MODE=false
      - COMIX_LOG_LEVEL=INFO
    volumes:
      - "/path/to/manga:/manga:ro"
    ports:
      - "31257:31257"
```

### Docker 환경 파일

```bash
# .env.docker
MANGA_DIRECTORY=/path/to/your/manga
COMIX_SERVER_PORT=31257
DEBUG_MODE=false
LOG_LEVEL=INFO
```

## 고급 설정

### 로깅 설정

#### 파일 로깅

```python
# app/utils/logging.py 수정

import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/comix-server/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file'],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

#### Syslog 로깅

```bash
# 환경 변수로 syslog 활성화
export COMIX_USE_SYSLOG=true
export COMIX_SYSLOG_ADDRESS=/dev/log
export COMIX_SYSLOG_FACILITY=local0
```

### 성능 튜닝

#### 메모리 설정

```bash
# 큰 파일 처리를 위한 메모리 설정
export COMIX_MAX_MEMORY_USAGE=1073741824  # 1GB
export COMIX_CHUNK_SIZE=8192  # 8KB 청크
```

#### 캐시 설정

```bash
# 파일 시스템 캐시 설정
export COMIX_ENABLE_CACHE=true
export COMIX_CACHE_SIZE=1000  # 캐시할 항목 수
export COMIX_CACHE_TTL=300    # 캐시 유효 시간 (초)
```

### 보안 설정

#### 경로 제한

```bash
# 접근 가능한 경로 제한
export COMIX_ALLOWED_PATHS="/manga,/comics,/books"
export COMIX_BLOCKED_PATTERNS="*.exe,*.bat,*.sh"
```

#### 네트워크 보안

```bash
# 허용된 IP 주소 (쉼표 구분)
export COMIX_ALLOWED_IPS="192.168.1.0/24,10.0.0.0/8"

# CORS 설정
export COMIX_CORS_ORIGINS="http://localhost:3000,https://myapp.com"
```

## 설정 검증

### 설정 확인 명령어

```bash
# 현재 설정 확인
python -c "from app.models.config import settings; print(settings.model_dump_json(indent=2))"

# 설정 유효성 검사
python -c "
from app.models.config import settings
from pathlib import Path

print(f'Manga Directory: {settings.manga_directory}')
print(f'Directory Exists: {Path(settings.manga_directory).exists()}')
print(f'Server Port: {settings.server_port}')
print(f'Debug Mode: {settings.debug_mode}')
"
```

### 설정 테스트 스크립트

```python
#!/usr/bin/env python3
# scripts/test-config.py

from pathlib import Path
from app.models.config import settings

def test_configuration():
    """설정 유효성 검사"""
    errors = []
    warnings = []
    
    # 만화 디렉토리 확인
    manga_dir = Path(settings.manga_directory)
    if not manga_dir.exists():
        errors.append(f"Manga directory does not exist: {manga_dir}")
    elif not manga_dir.is_dir():
        errors.append(f"Manga directory is not a directory: {manga_dir}")
    elif not os.access(manga_dir, os.R_OK):
        errors.append(f"Manga directory is not readable: {manga_dir}")
    
    # 포트 확인
    if not (1024 <= settings.server_port <= 65535):
        errors.append(f"Invalid port number: {settings.server_port}")
    
    # 로그 레벨 확인
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if settings.log_level.upper() not in valid_levels:
        errors.append(f"Invalid log level: {settings.log_level}")
    
    # 프로덕션 환경 경고
    if settings.debug_mode:
        warnings.append("Debug mode is enabled (not recommended for production)")
    
    # 결과 출력
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("✅ Configuration is valid")
    
    return len(errors) == 0

if __name__ == "__main__":
    import sys
    import os
    
    success = test_configuration()
    sys.exit(0 if success else 1)
```

## 문제 해결

### 일반적인 설정 문제

#### 1. 만화 디렉토리 접근 불가

```bash
# 문제: Permission denied
# 해결: 권한 확인 및 수정
ls -la /path/to/manga
sudo chown -R comix:comix /path/to/manga
sudo chmod -R 755 /path/to/manga
```

#### 2. 포트 충돌

```bash
# 문제: Address already in use
# 해결: 다른 포트 사용 또는 기존 프로세스 종료
sudo netstat -tlnp | grep 31257
sudo kill -9 <PID>
# 또는
export COMIX_SERVER_PORT=31258
```

#### 3. 환경 변수 인식 안됨

```bash
# 문제: 환경 변수가 적용되지 않음
# 해결: 변수명 확인 및 재시작
env | grep COMIX_
systemctl restart comix-server
```

### 설정 디버깅

#### 설정 값 추적

```python
# 설정 로딩 과정 디버깅
import os
from app.models.config import Settings

# 환경 변수 확인
print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith('COMIX_'):
        print(f"  {key}={value}")

# 최종 설정 값
settings = Settings()
print(f"\nFinal configuration:")
print(f"  manga_directory: {settings.manga_directory}")
print(f"  server_port: {settings.server_port}")
print(f"  debug_mode: {settings.debug_mode}")
```

#### 설정 파일 우선순위 확인

```bash
# .env 파일 확인
echo "=== .env file ==="
cat .env 2>/dev/null || echo "No .env file found"

# 환경 변수 확인
echo -e "\n=== Environment variables ==="
env | grep COMIX_ | sort

# 최종 설정 확인
echo -e "\n=== Final configuration ==="
python -c "from app.models.config import settings; print(settings.model_dump_json(indent=2))"
```

이 가이드를 참조하여 Comix Server를 다양한 환경에 맞게 최적으로 설정할 수 있습니다.