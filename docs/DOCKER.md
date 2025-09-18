# Docker 배포 가이드

Comix Server를 Docker를 사용하여 쉽게 배포하고 실행할 수 있습니다.

## 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 파일 복사 및 설정
cp .env.docker .env

# .env 파일을 편집하여 만화 컬렉션 경로 설정
# MANGA_DIRECTORY=/path/to/your/manga/collection
```

### 2. 서버 실행

```bash
# Docker Compose로 실행
docker-compose up -d

# 또는 스크립트 사용
./scripts/docker-run.sh start --detach
```

### 3. 접속 확인

브라우저에서 `http://localhost:31257`로 접속하여 서버가 정상 작동하는지 확인합니다.

## 상세 설정

### 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `MANGA_DIRECTORY` | `./manga` | 만화 컬렉션이 있는 호스트 디렉토리 |
| `COMIX_SERVER_PORT` | `31257` | 서버 포트 |
| `DEBUG_MODE` | `false` | 디버그 모드 활성화 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 (DEBUG, INFO, WARNING, ERROR) |

### Docker Compose 파일

#### 프로덕션 환경 (`docker-compose.yml`)
- 최적화된 멀티 스테이지 빌드
- 보안 강화 (non-root 사용자, 읽기 전용 볼륨)
- 리소스 제한 설정
- 헬스 체크 포함

#### 개발 환경 (`docker-compose.dev.yml`)
- 핫 리로드 지원
- 소스 코드 볼륨 마운트
- 디버그 포트 노출
- 개발용 의존성 포함

## 사용법

### 스크립트를 사용한 관리

#### 빌드
```bash
# 프로덕션 이미지 빌드
./scripts/docker-build.sh

# 개발 이미지 빌드
./scripts/docker-build.sh --dev

# 커스텀 이름과 태그로 빌드
./scripts/docker-build.sh --name my-comix --tag v1.0.0
```

#### 실행 및 관리
```bash
# 프로덕션 모드로 시작
./scripts/docker-run.sh start

# 개발 모드로 시작
./scripts/docker-run.sh start --dev

# 백그라운드에서 시작
./scripts/docker-run.sh start --detach

# 빌드 후 시작
./scripts/docker-run.sh start --build

# 서비스 중지
./scripts/docker-run.sh stop

# 서비스 재시작
./scripts/docker-run.sh restart

# 로그 확인
./scripts/docker-run.sh logs

# 상태 확인
./scripts/docker-run.sh status
```

### Docker Compose 직접 사용

#### 프로덕션 환경
```bash
# 서비스 시작
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

#### 개발 환경
```bash
# 개발 서비스 시작
docker-compose -f docker-compose.dev.yml up

# 백그라운드에서 시작
docker-compose -f docker-compose.dev.yml up -d

# 서비스 중지
docker-compose -f docker-compose.dev.yml down
```

## 볼륨 마운트

### 만화 컬렉션
```yaml
volumes:
  - "/path/to/your/manga:/manga:ro"
```
- 호스트의 만화 디렉토리를 컨테이너의 `/manga`에 읽기 전용으로 마운트
- 보안을 위해 읽기 전용(`:ro`) 권한 사용 권장

### 설정 파일 (선택사항)
```yaml
volumes:
  - "./config:/app/config:ro"
```

## 네트워크 설정

### 포트 매핑
- 기본 포트: `31257`
- 개발 모드 디버그 포트: `5678`

### 방화벽 설정
```bash
# UFW 사용 시
sudo ufw allow 31257

# iptables 사용 시
sudo iptables -A INPUT -p tcp --dport 31257 -j ACCEPT
```

## 보안 고려사항

### 컨테이너 보안
- Non-root 사용자로 실행
- 읽기 전용 파일 시스템
- 최소 권한 원칙 적용
- `no-new-privileges` 보안 옵션 활성화

### 네트워크 보안
- 필요한 포트만 노출
- 내부 네트워크 사용
- 리버스 프록시 사용 권장

### 파일 시스템 보안
```bash
# 만화 디렉토리 권한 설정
chmod -R 755 /path/to/manga
chown -R root:root /path/to/manga
```

## 성능 최적화

### 리소스 제한
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
    reservations:
      memory: 256M
      cpus: '0.5'
```

### 로깅 설정
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 모니터링

### 헬스 체크
```bash
# 컨테이너 헬스 상태 확인
docker ps

# 상세 헬스 체크 정보
docker inspect comix-server | grep -A 10 Health
```

### 리소스 사용량 모니터링
```bash
# 실시간 리소스 사용량
docker stats comix-server

# 로그 모니터링
docker logs -f comix-server
```

## 문제 해결

### 일반적인 문제

#### 1. 포트 충돌
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep 31257

# 다른 포트 사용
COMIX_SERVER_PORT=31258 docker-compose up -d
```

#### 2. 권한 문제
```bash
# 만화 디렉토리 권한 확인
ls -la /path/to/manga

# 권한 수정
sudo chmod -R 755 /path/to/manga
```

#### 3. 메모리 부족
```bash
# 메모리 사용량 확인
docker stats --no-stream

# 메모리 제한 증가
# docker-compose.yml에서 memory 값 조정
```

### 디버깅

#### 개발 모드로 실행
```bash
# 개발 모드로 상세 로그와 함께 실행
./scripts/docker-run.sh start --dev --logs
```

#### 컨테이너 내부 접근
```bash
# 실행 중인 컨테이너에 접속
docker exec -it comix-server /bin/bash

# 개발 컨테이너에 접속
docker exec -it comix-server-dev /bin/bash
```

#### 로그 분석
```bash
# 전체 로그 확인
docker logs comix-server

# 실시간 로그 모니터링
docker logs -f comix-server

# 특정 시간 이후 로그
docker logs --since="2024-01-01T00:00:00" comix-server
```

## 업데이트

### 이미지 업데이트
```bash
# 새 이미지 빌드
./scripts/docker-build.sh

# 서비스 재시작
./scripts/docker-run.sh restart
```

### 설정 업데이트
```bash
# 설정 변경 후 재시작
docker-compose restart
```

## 백업 및 복원

### 설정 백업
```bash
# 환경 설정 백업
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

### 로그 백업
```bash
# 로그 백업
docker logs comix-server > comix-server.log.$(date +%Y%m%d)
```