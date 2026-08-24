"""
인증 미들웨어

HTTP Basic Authentication을 구현합니다.
"""

import base64
import secrets
import time
from typing import Dict, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.models.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 브루트포스 방어 상수
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
MAX_TRACKED_CLIENTS = 1024


def _passwords_match(candidate: str, expected: str) -> bool:
    """상수 시간 패스워드 비교

    secrets.compare_digest는 non-ASCII 문자열을 거부하므로(TypeError)
    항상 bytes로 변환해서 비교한다. 한글 패스워드도 정상 동작한다.
    """
    return secrets.compare_digest(
        candidate.encode("utf-8"), expected.encode("utf-8")
    )


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """HTTP Basic Authentication 미들웨어"""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        # AirComix 앱이 패스워드 입력 전에 호출하는 최소 경로 + 컨테이너 헬스체크만 제외한다.
        # 만화 목록(/comix/...)은 루트 목록까지 포함해 전부 인증 대상이다.
        self.exclude_paths = exclude_paths or [
            "/health",
            "/",  # 루트 디렉토리 이름
            "/welcome.102",  # 서버 정보
        ]
        # ponytail: 프로세스 로컬 실패 카운터. gunicorn 워커별로 독립이고 재시작 시 초기화된다.
        #           워커 간 정밀한 제한이 필요해지면 Redis 같은 공유 저장소로 옮긴다.
        self._failed_attempts: Dict[str, Tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next):
        """요청 처리 및 인증 확인"""

        # 인증이 비활성화된 경우 통과
        if not settings.enable_auth:
            return await call_next(request)

        # 제외 경로 확인
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_ip = self._client_ip(request)

        # 연속 실패로 잠긴 클라이언트 차단
        retry_after = self._lockout_remaining(client_ip)
        if retry_after > 0:
            logger.warning(
                f"인증 시도 제한: {client_ip} {request.method} {request.url.path} "
                f"({retry_after}초 후 재시도 가능)"
            )
            return self._too_many_requests_response(retry_after)

        password = self._extract_password(request)

        if password is None:
            logger.debug(f"인증 헤더 없음/파싱 실패: {request.method} {request.url.path}")
            return self._unauthorized_response()

        if not self._verify_password(password):
            self._record_failure(client_ip)
            logger.warning(f"패스워드 불일치: {client_ip} {request.method} {request.url.path}")
            return self._unauthorized_response()

        # 인증 성공
        self._clear_failures(client_ip)
        logger.debug(f"인증 성공: {request.method} {request.url.path}")
        return await call_next(request)

    @staticmethod
    def _client_ip(request: Request) -> str:
        """요청 클라이언트 IP 추출"""
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _extract_password(request: Request) -> Optional[str]:
        """Authorization 헤더에서 패스워드 추출 (실패 시 None)"""
        return get_basic_auth_password(request)

    def _verify_password(self, password: str) -> bool:
        """패스워드 확인 (.htaccess 방식)"""
        if not settings.auth_password:
            return False

        return _passwords_match(password, settings.auth_password)

    def _lockout_remaining(self, client_ip: str) -> int:
        """남은 잠금 시간(초). 잠겨 있지 않으면 0"""
        record = self._failed_attempts.get(client_ip)
        if not record:
            return 0

        count, last_failure = record
        if count < MAX_FAILED_ATTEMPTS:
            return 0

        elapsed = time.monotonic() - last_failure
        if elapsed >= LOCKOUT_SECONDS:
            # 잠금 기간이 지났으면 카운터 초기화
            self._failed_attempts.pop(client_ip, None)
            return 0

        return int(LOCKOUT_SECONDS - elapsed) + 1

    def _record_failure(self, client_ip: str) -> None:
        """인증 실패 기록"""
        now = time.monotonic()
        count, _ = self._failed_attempts.get(client_ip, (0, now))
        self._failed_attempts[client_ip] = (count + 1, now)

        if len(self._failed_attempts) > MAX_TRACKED_CLIENTS:
            self._prune_expired(now)

    def _clear_failures(self, client_ip: str) -> None:
        """인증 성공 시 실패 카운터 제거"""
        self._failed_attempts.pop(client_ip, None)

    def _prune_expired(self, now: float) -> None:
        """잠금 기간이 지난 기록 정리 (메모리 무한 증가 방지)"""
        self._failed_attempts = {
            ip: record
            for ip, record in self._failed_attempts.items()
            if now - record[1] < LOCKOUT_SECONDS
        }

    def _unauthorized_response(self) -> Response:
        """401 Unauthorized 응답 생성"""
        return Response(
            content="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic realm=\"AirComix\""}
        )

    def _too_many_requests_response(self, retry_after: int) -> Response:
        """429 Too Many Requests 응답 생성"""
        return Response(
            content="Too Many Requests",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={
                "Retry-After": str(retry_after),
                "WWW-Authenticate": "Basic realm=\"AirComix\"",
            },
        )


def get_basic_auth_password(request: Request) -> Optional[str]:
    """요청에서 Basic Auth 패스워드 추출 (.htaccess 방식)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    try:
        scheme, credentials = auth_header.split(" ", 1)
        if scheme.lower() != "basic":
            return None

        decoded = base64.b64decode(credentials).decode("utf-8")
        # .htaccess 방식: 패스워드만 사용
        if ":" in decoded:
            _, password = decoded.split(":", 1)
        else:
            password = decoded
        return password

    except (ValueError, UnicodeDecodeError):
        return None


def verify_auth_password(password: str) -> bool:
    """패스워드 인증 확인 (.htaccess 방식)"""
    if not settings.enable_auth:
        return True

    if not settings.auth_password:
        return False

    return _passwords_match(password, settings.auth_password)


# FastAPI Dependency로 사용할 수 있는 인증 함수
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """현재 사용자 인증 (FastAPI Dependency) - .htaccess 방식"""
    if not settings.enable_auth:
        return "anonymous"

    # .htaccess 방식: 패스워드만 확인
    if not verify_auth_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return "authenticated"
