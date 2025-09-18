"""
Gunicorn 프로덕션 설정

Comix Server를 프로덕션 환경에서 실행하기 위한 Gunicorn 설정
"""

import multiprocessing
import os
from pathlib import Path

# 서버 소켓
bind = f"0.0.0.0:{os.getenv('COMIX_SERVER_PORT', '31257')}"
backlog = 2048

# 워커 프로세스
workers = int(os.getenv('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 120
keepalive = 2

# 로깅
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv('COMIX_LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 프로세스 이름
proc_name = "comix-server"

# 보안
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# 성능 튜닝
worker_tmp_dir = "/dev/shm"  # 메모리 기반 임시 디렉토리 사용

# 프로세스 관리
pidfile = "/tmp/gunicorn.pid"
user = os.getenv('GUNICORN_USER', None)
group = os.getenv('GUNICORN_GROUP', None)
tmp_upload_dir = None

# 개발 모드 설정
if os.getenv('COMIX_DEBUG_MODE', 'false').lower() == 'true':
    reload = True
    loglevel = 'debug'
else:
    reload = False

# SSL 설정 (필요시)
keyfile = os.getenv('SSL_KEYFILE', None)
certfile = os.getenv('SSL_CERTFILE', None)

# 헬스 체크를 위한 설정
def when_ready(server):
    """서버가 준비되었을 때 실행되는 콜백"""
    server.log.info("Comix Server is ready to serve requests")

def worker_int(worker):
    """워커가 SIGINT를 받았을 때 실행되는 콜백"""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """워커가 포크되기 전에 실행되는 콜백"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """워커가 포크된 후에 실행되는 콜백"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    """서버가 재시작되기 전에 실행되는 콜백"""
    server.log.info("Forked child, re-executing.")

def on_exit(server):
    """서버가 종료될 때 실행되는 콜백"""
    server.log.info("Comix Server is shutting down")

def on_reload(server):
    """서버가 리로드될 때 실행되는 콜백"""
    server.log.info("Comix Server is reloading")