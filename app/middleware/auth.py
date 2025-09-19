"""
인증 미들웨어

HTTP Basic Authentication을 구현합니다.
"""

import base64
import secrets
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.models.config import settings


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """HTTP Basic Authentication 미들웨어"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """요청 처리 및 인증 확인"""
        
        # 인증이 비활성화된 경우 통과
        if not settings.enable_auth:
            return await call_next(request)
        
        # 제외 경로 확인
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Authorization 헤더 확인
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._unauthorized_response()
        
        # Basic 인증 확인
        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "basic":
                return self._unauthorized_response()
            
            # Base64 디코딩
            decoded = base64.b64decode(credentials).decode("utf-8")
            # .htaccess 방식: 패스워드만 확인 (username:password 형태에서 password 부분만 사용)
            if ":" in decoded:
                _, password = decoded.split(":", 1)
            else:
                password = decoded
            
            # 패스워드 확인
            if not self._verify_password(password):
                return self._unauthorized_response()
            
        except (ValueError, UnicodeDecodeError):
            return self._unauthorized_response()
        
        # 인증 성공, 요청 계속 처리
        return await call_next(request)
    
    def _verify_password(self, password: str) -> bool:
        """패스워드 확인 (.htaccess 방식)"""
        if not settings.auth_password:
            return False
        
        # 타이밍 공격 방지를 위한 상수 시간 비교
        return secrets.compare_digest(password, settings.auth_password)
    
    def _unauthorized_response(self) -> Response:
        """401 Unauthorized 응답 생성"""
        return Response(
            content="Unauthorized",
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic realm=\"AirComix\""}
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
    
    # 타이밍 공격 방지를 위한 상수 시간 비교
    return secrets.compare_digest(password, settings.auth_password)


# FastAPI Dependency로 사용할 수 있는 인증 함수
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = security):
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