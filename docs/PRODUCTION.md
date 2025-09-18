# 프로덕션 배포 가이드

Comix Server를 프로덕션 환경에 안전하고 효율적으로 배포하는 방법을 설명합니다.

## 빠른 시작

### 자동 배포 (권장)

```bash
# 저장소 클론
git clone https://github.com/comix-server/comix-server-python.git
cd comix-server-python

# 프로덕션 배포 실행 (root 권한 필요)
sudo ./scripts/deploy-production.sh

# 배포 후 상태 확인
sudo ./scripts/check-production.sh
```

### 수동 배포

자세한 수동 배포 과정은 아래 섹션을 참조하세요.

## 시스템 요구사항

### 최소 요구사항
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **CPU**: 1 vCPU
- **RAM**: 512MB
- **Storage**: 1GB (애플리케이션) + 만화 컬렉션 크기
- **Python**: 3.11+

### 권장 사양
- **CPU**: 2+ vCPU
- **RAM**: 2GB+
- **Storage**: SSD 권장
- **Network**: 100Mbps+

### 필수 패키지
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev \
    build-essential unrar-free nginx supervisor curl git

# CentOS/RHEL/Fedora
sudo dnf install -y python3.11 python3.11-devel gcc gcc-c++ make \
    unrar nginx supervisor curl git
```

## 배포 아키텍처

```
[Internet] → [Nginx] → [Gunicorn] → [FastAPI App]
                ↓
            [Static Files]
                ↓
            [Manga Files]
```

### 구성 요소
- **Nginx**: 리버스 프록시, SSL 터미네이션, 정적 파일 서빙
- **Gunicorn**: WSGI 서버, 프로세스 관리
- **FastAPI**: 애플리케이션 서버
- **Systemd**: 서비스 관리 및 자동 시작

## 수동 배포 과정

### 1. 사용자 및 디렉토리 설정

```bash
# 서비스 사용자 생성
sudo groupadd --system comix
sudo useradd --system --gid comix --home-dir /opt/comix-server \
    --no-create-home --shell /bin/false comix

# 디렉토리 생성
sudo mkdir -p /opt/comix-server
sudo mkdir -p /var/lib/comix/manga
sudo mkdir -p /etc/comix-server
sudo mkdir -p /var/log/comix-server

# 권한 설정
sudo chown -R comix:comix /opt/comix-server
sudo chown -R comix:comix /var/lib/comix
sudo chown -R comix:comix /var/log/comix-server
```

### 2. 애플리케이션 설치

```bash
# 소스 코드 복사
sudo cp -r . /opt/comix-server/
cd /opt/comix-server

# 가상 환경 생성
sudo -u comix python3.11 -m venv .venv

# 의존성 설치
sudo -u comix .venv/bin/pip install --upgrade pip setuptools wheel
sudo -u comix .venv/bin/pip install -e .
sudo -u comix .venv/bin/pip install gunicorn
```

### 3. 설정 파일 생성

```bash
# 환경 설정 파일
sudo tee /etc/comix-server/comix-server.env << EOF
COMIX_MANGA_DIRECTORY=/var/lib/comix/manga
COMIX_SERVER_HOST=127.0.0.1
COMIX_SERVER_PORT=31257
COMIX_DEBUG_MODE=false
COMIX_LOG_LEVEL=INFO
GUNICORN_WORKERS=4
EOF

# 권한 설정
sudo chmod 640 /etc/comix-server/comix-server.env
sudo chown root:comix /etc/comix-server/comix-server.env
```

### 4. Systemd 서비스 설정

```bash
# 서비스 파일 복사
sudo cp deployment/systemd/comix-server.service /etc/systemd/system/

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable comix-server
sudo systemctl start comix-server
```

### 5. Nginx 설정

```bash
# Nginx 설정 복사
sudo cp deployment/nginx/comix-server.conf /etc/nginx/sites-available/

# 사이트 활성화 (Ubuntu/Debian)
sudo ln -sf /etc/nginx/sites-available/comix-server.conf /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

## 설정 관리

### 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `COMIX_MANGA_DIRECTORY` | `/var/lib/comix/manga` | 만화 컬렉션 디렉토리 |
| `COMIX_SERVER_HOST` | `127.0.0.1` | 바인드 호스트 |
| `COMIX_SERVER_PORT` | `31257` | 서비스 포트 |
| `COMIX_DEBUG_MODE` | `false` | 디버그 모드 |
| `COMIX_LOG_LEVEL` | `INFO` | 로그 레벨 |
| `GUNICORN_WORKERS` | `4` | Gunicorn 워커 수 |

### Gunicorn 설정

`gunicorn.conf.py` 파일에서 다음 설정을 조정할 수 있습니다:

```python
# 워커 프로세스 수 (CPU 코어 수 * 2 + 1)
workers = multiprocessing.cpu_count() * 2 + 1

# 워커 클래스
worker_class = "uvicorn.workers.UvicornWorker"

# 연결 설정
worker_connections = 1000
max_requests = 1000
timeout = 120
```

### Nginx 설정

주요 설정 포인트:

```nginx
# 업스트림 서버
upstream comix_server {
    server 127.0.0.1:31257;
    keepalive 32;
}

# SSL 설정
ssl_certificate /path/to/certificate.crt;
ssl_certificate_key /path/to/private.key;

# 프록시 설정
proxy_pass http://comix_server;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
```

## SSL/TLS 설정

### Let's Encrypt 사용

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d your-domain.com

# 자동 갱신 설정
sudo crontab -e
# 다음 라인 추가:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 자체 서명 인증서

```bash
# 인증서 생성
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/comix-server.key \
    -out /etc/ssl/certs/comix-server.crt

# 권한 설정
sudo chmod 600 /etc/ssl/private/comix-server.key
sudo chmod 644 /etc/ssl/certs/comix-server.crt
```

## 모니터링 및 로깅

### 로그 파일 위치

```
/var/log/comix-server/
├── comix-server.log          # 애플리케이션 로그
├── comix-server-error.log    # 에러 로그
└── supervisor.log            # Supervisor 로그 (사용시)
```

### 로그 로테이션

```bash
# logrotate 설정
sudo tee /etc/logrotate.d/comix-server << EOF
/var/log/comix-server/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 comix comix
    postrotate
        systemctl reload comix-server
    endscript
}
EOF
```

### 시스템 모니터링

```bash
# 서비스 상태 확인
systemctl status comix-server

# 실시간 로그 확인
journalctl -u comix-server -f

# 리소스 사용량 확인
htop
iostat -x 1
```

### 헬스 체크

```bash
# 기본 헬스 체크
curl http://localhost:31257/health

# 상세 상태 확인
./scripts/check-production.sh
```

## 성능 최적화

### Gunicorn 튜닝

```python
# CPU 집약적 작업이 많은 경우
workers = multiprocessing.cpu_count() + 1

# I/O 집약적 작업이 많은 경우
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000
```

### Nginx 튜닝

```nginx
# 워커 프로세스 수
worker_processes auto;

# 연결 수 제한
events {
    worker_connections 1024;
    use epoll;
}

# 버퍼 크기 조정
client_body_buffer_size 128k;
client_max_body_size 10m;
```

### 시스템 튜닝

```bash
# 파일 디스크립터 제한 증가
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 커널 파라미터 조정
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

## 보안 설정

### 방화벽 설정

```bash
# UFW 사용시
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# firewalld 사용시
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 파일 권한

```bash
# 애플리케이션 파일
sudo find /opt/comix-server -type f -exec chmod 644 {} \;
sudo find /opt/comix-server -type d -exec chmod 755 {} \;
sudo chmod +x /opt/comix-server/scripts/*.sh

# 설정 파일
sudo chmod 640 /etc/comix-server/comix-server.env
sudo chown root:comix /etc/comix-server/comix-server.env

# 만화 디렉토리 (읽기 전용)
sudo chmod -R 755 /var/lib/comix/manga
sudo chown -R comix:comix /var/lib/comix/manga
```

### SELinux 설정 (RHEL/CentOS)

```bash
# SELinux 컨텍스트 설정
sudo setsebool -P httpd_can_network_connect 1
sudo semanage port -a -t http_port_t -p tcp 31257

# 파일 컨텍스트 설정
sudo semanage fcontext -a -t httpd_exec_t "/opt/comix-server/.*"
sudo restorecon -R /opt/comix-server
```

## 백업 및 복구

### 백업 대상

```bash
# 설정 파일
/etc/comix-server/
/etc/systemd/system/comix-server.service
/etc/nginx/sites-available/comix-server.conf

# 애플리케이션 (선택사항)
/opt/comix-server/

# 로그 (선택사항)
/var/log/comix-server/
```

### 백업 스크립트

```bash
#!/bin/bash
# 백업 스크립트 예제

BACKUP_DIR="/backup/comix-server"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 설정 백업
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /etc/comix-server/ \
    /etc/systemd/system/comix-server.service \
    /etc/nginx/sites-available/comix-server.conf

# 로그 백업 (선택사항)
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /var/log/comix-server/

# 오래된 백업 정리 (30일 이상)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

## 업데이트 및 유지보수

### 애플리케이션 업데이트

```bash
# 1. 서비스 중지
sudo systemctl stop comix-server

# 2. 백업 생성
sudo cp -r /opt/comix-server /opt/comix-server.backup

# 3. 새 버전 배포
cd /opt/comix-server
sudo -u comix git pull
sudo -u comix .venv/bin/pip install -e .

# 4. 서비스 시작
sudo systemctl start comix-server

# 5. 상태 확인
sudo systemctl status comix-server
```

### 롤백 절차

```bash
# 1. 서비스 중지
sudo systemctl stop comix-server

# 2. 백업에서 복원
sudo rm -rf /opt/comix-server
sudo mv /opt/comix-server.backup /opt/comix-server

# 3. 서비스 시작
sudo systemctl start comix-server
```

## 문제 해결

### 일반적인 문제

#### 1. 서비스가 시작되지 않음

```bash
# 로그 확인
journalctl -u comix-server -n 50

# 설정 파일 확인
sudo -u comix /opt/comix-server/.venv/bin/python -c "from app.main import create_app; create_app()"

# 권한 확인
ls -la /opt/comix-server
ls -la /var/lib/comix/manga
```

#### 2. 포트 충돌

```bash
# 포트 사용 확인
sudo netstat -tlnp | grep 31257
sudo lsof -i :31257

# 다른 포트 사용
sudo systemctl edit comix-server
# 다음 내용 추가:
# [Service]
# Environment="COMIX_SERVER_PORT=31258"
```

#### 3. 권한 문제

```bash
# 파일 권한 재설정
sudo chown -R comix:comix /opt/comix-server
sudo chown -R comix:comix /var/lib/comix
sudo chown -R comix:comix /var/log/comix-server
```

#### 4. 메모리 부족

```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head

# Gunicorn 워커 수 조정
# gunicorn.conf.py에서 workers 값 감소
```

### 디버깅 도구

```bash
# 상세 로그 활성화
sudo systemctl edit comix-server
# 다음 내용 추가:
# [Service]
# Environment="COMIX_LOG_LEVEL=DEBUG"

# 프로세스 모니터링
htop
iotop
nethogs

# 네트워크 연결 확인
ss -tlnp | grep 31257
curl -v http://localhost:31257/health
```

## 성능 벤치마킹

### 기본 성능 테스트

```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:31257/

# wrk
wrk -t12 -c400 -d30s http://localhost:31257/

# 이미지 스트리밍 테스트
curl -o /dev/null -s -w "%{time_total}\n" http://localhost:31257/manga/test.jpg
```

### 모니터링 메트릭

- **응답 시간**: < 100ms (디렉토리 목록)
- **처리량**: > 100 req/sec
- **메모리 사용량**: < 512MB (기본 설정)
- **CPU 사용률**: < 50% (정상 부하)

이 가이드를 따라 Comix Server를 안전하고 효율적으로 프로덕션 환경에 배포할 수 있습니다.