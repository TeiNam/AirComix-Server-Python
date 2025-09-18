# 문제 해결 가이드

Comix Server 사용 중 발생할 수 있는 일반적인 문제들과 해결 방법을 설명합니다.

## 🔍 진단 도구

### 기본 상태 확인

```bash
# 서버 상태 확인
curl http://localhost:31257/health

# 프로덕션 환경 체크 (프로덕션 배포 시)
sudo ./scripts/check-production.sh

# 서비스 상태 (systemd 사용 시)
systemctl status comix-server

# 로그 확인
journalctl -u comix-server -f
```

### 설정 확인

```bash
# 현재 설정 출력
python -c "from app.models.config import settings; print(settings.model_dump_json(indent=2))"

# 환경 변수 확인
env | grep COMIX_

# 만화 디렉토리 접근 확인
ls -la $COMIX_MANGA_DIRECTORY
```

## 🚨 일반적인 문제들

### 1. 서버가 시작되지 않음

#### 증상
```bash
$ comix-server
Error: [Errno 98] Address already in use
```

#### 원인
- 포트가 이미 사용 중
- 권한 부족
- 설정 오류

#### 해결 방법

**포트 충돌 확인**
```bash
# 포트 사용 확인
sudo netstat -tlnp | grep 31257
sudo lsof -i :31257

# 프로세스 종료
sudo kill -9 <PID>

# 다른 포트 사용
export COMIX_SERVER_PORT=31258
comix-server
```

**권한 문제**
```bash
# 포트 1024 미만 사용 시 root 권한 필요
sudo comix-server

# 또는 1024 이상 포트 사용
export COMIX_SERVER_PORT=8080
comix-server
```

**설정 검증**
```bash
# 설정 파일 구문 확인
python -c "from app.models.config import Settings; Settings()"

# 만화 디렉토리 확인
ls -la "$COMIX_MANGA_DIRECTORY"
```

---

### 2. 만화 디렉토리에 접근할 수 없음

#### 증상
```
HTTP 503 Service Unavailable
Manga directory not accessible
```

#### 원인
- 디렉토리가 존재하지 않음
- 권한 부족
- 잘못된 경로

#### 해결 방법

**디렉토리 확인**
```bash
# 디렉토리 존재 확인
ls -la "$COMIX_MANGA_DIRECTORY"

# 디렉토리 생성
sudo mkdir -p "$COMIX_MANGA_DIRECTORY"
sudo chown comix:comix "$COMIX_MANGA_DIRECTORY"
sudo chmod 755 "$COMIX_MANGA_DIRECTORY"
```

**권한 수정**
```bash
# 읽기 권한 부여
sudo chmod -R 755 "$COMIX_MANGA_DIRECTORY"

# 소유자 변경 (프로덕션 환경)
sudo chown -R comix:comix "$COMIX_MANGA_DIRECTORY"
```

**경로 확인**
```bash
# 절대 경로 사용
export COMIX_MANGA_DIRECTORY="/home/user/manga"

# 심볼릭 링크 확인
ls -la "$COMIX_MANGA_DIRECTORY"
readlink -f "$COMIX_MANGA_DIRECTORY"
```

---

### 3. 아카이브 파일을 열 수 없음

#### 증상
```
HTTP 500 Internal Server Error
Archive processing error
```

#### 원인
- 손상된 아카이브 파일
- unrar 도구 미설치 (RAR 파일)
- 지원되지 않는 압축 형식

#### 해결 방법

**RAR 지원 설치**
```bash
# Ubuntu/Debian
sudo apt-get install unrar-free

# CentOS/RHEL
sudo yum install unrar

# macOS
brew install unrar
```

**아카이브 파일 검증**
```bash
# ZIP 파일 테스트
unzip -t file.zip

# RAR 파일 테스트
unrar t file.rar

# 파일 형식 확인
file file.cbz
```

**손상된 파일 처리**
```bash
# 손상된 파일 찾기
find "$COMIX_MANGA_DIRECTORY" -name "*.zip" -exec unzip -t {} \; 2>&1 | grep -B1 "bad"

# 손상된 파일 격리
mkdir -p "$COMIX_MANGA_DIRECTORY/.corrupted"
mv corrupted_file.zip "$COMIX_MANGA_DIRECTORY/.corrupted/"
```

---

### 4. 이미지가 표시되지 않음

#### 증상
- 이미지 로딩 실패
- 빈 화면 또는 깨진 이미지 아이콘

#### 원인
- 지원되지 않는 이미지 형식
- 파일 권한 문제
- 문자 인코딩 문제

#### 해결 방법

**지원 형식 확인**
```bash
# 지원되는 이미지 형식
echo $COMIX_IMAGE_EXTENSIONS

# 파일 형식 확인
file image.jpg
identify image.jpg  # ImageMagick 필요
```

**권한 확인**
```bash
# 이미지 파일 권한 확인
ls -la "$COMIX_MANGA_DIRECTORY"/*.jpg

# 권한 수정
chmod 644 "$COMIX_MANGA_DIRECTORY"/*.jpg
```

**인코딩 문제**
```bash
# 파일명 인코딩 확인
ls -la | hexdump -C

# 파일명 변환 (예: EUC-KR → UTF-8)
convmv -f euc-kr -t utf8 --notest -r "$COMIX_MANGA_DIRECTORY"
```

---

### 5. 성능 문제

#### 증상
- 느린 응답 시간
- 높은 메모리 사용량
- CPU 사용률 100%

#### 원인
- 부적절한 워커 수 설정
- 큰 파일 처리
- 메모리 부족

#### 해결 방법

**워커 수 조정**
```python
# gunicorn.conf.py
import multiprocessing

# CPU 집약적 작업
workers = multiprocessing.cpu_count() + 1

# I/O 집약적 작업
workers = multiprocessing.cpu_count() * 2 + 1
```

**메모리 최적화**
```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head

# 스왑 설정 확인
swapon --show

# 워커 수 감소
export GUNICORN_WORKERS=2
```

**파일 시스템 최적화**
```bash
# SSD 사용 권장
df -h "$COMIX_MANGA_DIRECTORY"

# 파일 시스템 캐시 확인
cat /proc/meminfo | grep -i cache

# 불필요한 파일 정리
find "$COMIX_MANGA_DIRECTORY" -name "Thumbs.db" -delete
find "$COMIX_MANGA_DIRECTORY" -name ".DS_Store" -delete
```

---

### 6. 문자 인코딩 문제

#### 증상
- 한글/일본어 파일명이 깨져 보임
- 아카이브 내 파일명 오류

#### 원인
- 잘못된 문자 인코딩
- 시스템 로케일 설정 문제

#### 해결 방법

**시스템 로케일 확인**
```bash
# 현재 로케일 확인
locale

# UTF-8 로케일 설정
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

**파일명 변환**
```bash
# 파일명 인코딩 확인
ls -la | od -c

# 파일명 변환 도구 설치
sudo apt-get install convmv

# EUC-KR → UTF-8 변환
convmv -f euc-kr -t utf8 --notest -r "$COMIX_MANGA_DIRECTORY"
```

**Python 인코딩 설정**
```python
# 환경 변수 설정
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

---

### 7. Docker 관련 문제

#### 증상
- 컨테이너가 시작되지 않음
- 볼륨 마운트 실패

#### 원인
- 잘못된 볼륨 경로
- 권한 문제
- 포트 충돌

#### 해결 방법

**볼륨 마운트 확인**
```bash
# 호스트 경로 확인
ls -la /path/to/manga

# 컨테이너 내부 확인
docker exec -it comix-server ls -la /manga

# 권한 문제 해결
sudo chown -R 1000:1000 /path/to/manga  # Docker 사용자 ID
```

**포트 매핑 확인**
```bash
# 포트 사용 확인
docker ps
netstat -tlnp | grep 31257

# 다른 포트 사용
docker run -p 8080:31257 comix-server
```

**로그 확인**
```bash
# 컨테이너 로그
docker logs comix-server

# 실시간 로그
docker logs -f comix-server
```

---

### 8. 네트워크 연결 문제

#### 증상
- AirComix 앱에서 서버에 연결할 수 없음
- 외부에서 접근 불가

#### 원인
- 방화벽 차단
- 네트워크 설정 문제
- 잘못된 IP 주소

#### 해결 방법

**방화벽 설정**
```bash
# UFW (Ubuntu)
sudo ufw allow 31257/tcp
sudo ufw status

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=31257/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 31257 -j ACCEPT
```

**네트워크 확인**
```bash
# 서버 바인딩 확인
netstat -tlnp | grep 31257

# 외부 접근 테스트
curl http://server-ip:31257/health

# 네트워크 인터페이스 확인
ip addr show
```

**호스트 설정**
```bash
# 모든 인터페이스에 바인딩
export COMIX_SERVER_HOST=0.0.0.0

# 특정 IP에만 바인딩
export COMIX_SERVER_HOST=192.168.1.100
```

---

## 🔧 고급 디버깅

### 로그 분석

#### 로그 레벨 증가
```bash
# 디버그 로그 활성화
export COMIX_LOG_LEVEL=DEBUG
export COMIX_DEBUG_MODE=true

# 서비스 재시작
systemctl restart comix-server
```

#### 로그 파일 위치
```bash
# 시스템 로그
journalctl -u comix-server -f

# 애플리케이션 로그
tail -f /var/log/comix-server/comix-server.log

# 에러 로그
tail -f /var/log/comix-server/comix-server-error.log
```

### 성능 프로파일링

#### 메모리 사용량 모니터링
```bash
# 실시간 메모리 사용량
watch -n 1 'ps aux --sort=-%mem | grep comix'

# 메모리 프로파일링 (Python)
pip install memory-profiler
python -m memory_profiler app/main.py
```

#### CPU 사용량 분석
```bash
# CPU 사용량 모니터링
htop
top -p $(pgrep -f comix)

# 프로세스 트리
pstree -p $(pgrep -f comix)
```

### 네트워크 디버깅

#### 연결 상태 확인
```bash
# 활성 연결 확인
ss -tlnp | grep 31257
netstat -an | grep 31257

# 연결 테스트
telnet localhost 31257
nc -zv localhost 31257
```

#### 패킷 캡처
```bash
# tcpdump로 패킷 캡처
sudo tcpdump -i any port 31257

# Wireshark 사용 (GUI)
wireshark
```

### 파일 시스템 디버깅

#### 파일 접근 추적
```bash
# strace로 시스템 콜 추적
strace -e trace=file -p $(pgrep -f comix)

# inotify로 파일 변경 감시
inotifywait -m -r "$COMIX_MANGA_DIRECTORY"
```

#### 디스크 I/O 모니터링
```bash
# I/O 통계
iostat -x 1

# 디스크 사용량
df -h "$COMIX_MANGA_DIRECTORY"
du -sh "$COMIX_MANGA_DIRECTORY"/*
```

## 📞 지원 요청

문제가 해결되지 않는 경우 다음 정보와 함께 지원을 요청하세요:

### 필수 정보

```bash
# 시스템 정보 수집 스크립트
#!/bin/bash

echo "=== System Information ==="
uname -a
cat /etc/os-release

echo -e "\n=== Python Version ==="
python --version
python -c "import sys; print(sys.path)"

echo -e "\n=== Comix Server Configuration ==="
python -c "from app.models.config import settings; print(settings.model_dump_json(indent=2))"

echo -e "\n=== Environment Variables ==="
env | grep COMIX_ | sort

echo -e "\n=== Service Status ==="
systemctl status comix-server --no-pager

echo -e "\n=== Recent Logs ==="
journalctl -u comix-server --no-pager -n 50

echo -e "\n=== Network Status ==="
netstat -tlnp | grep 31257

echo -e "\n=== Disk Usage ==="
df -h "$COMIX_MANGA_DIRECTORY"

echo -e "\n=== File Permissions ==="
ls -la "$COMIX_MANGA_DIRECTORY" | head -10
```

### 지원 채널

- 🐛 **버그 리포트**: [GitHub Issues](https://github.com/comix-server/comix-server-python/issues)
- 💬 **질문 및 토론**: [GitHub Discussions](https://github.com/comix-server/comix-server-python/discussions)
- 📧 **이메일**: support@comix-server.com
- 📖 **문서**: [공식 문서](https://docs.comix-server.com)

### 버그 리포트 템플릿

```markdown
## 문제 설명
간단한 문제 설명

## 재현 단계
1. 
2. 
3. 

## 예상 동작
무엇이 일어나야 하는지

## 실제 동작
실제로 무엇이 일어났는지

## 환경 정보
- OS: 
- Python 버전: 
- Comix Server 버전: 
- 배포 방식: (Docker/Native/etc)

## 로그
```
관련 로그 내용
```

## 추가 정보
스크린샷, 설정 파일 등
```

이 가이드를 통해 대부분의 문제를 해결할 수 있습니다. 추가적인 도움이 필요한 경우 언제든지 지원 채널을 이용해 주세요.