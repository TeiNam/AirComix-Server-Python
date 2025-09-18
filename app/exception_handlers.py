"""
글로벌 예외 핸들러

FastAPI 애플리케이션에서 발생하는 모든 예외를 처리합니다.
"""

import traceback
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import ComixServerException
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def comix_server_exception_handler(
    request: Request, 
    exc: ComixServerException
) -> Union[JSONResponse, PlainTextResponse]:
    """
    Comix Server 커스텀 예외 핸들러
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 ComixServerException
        
    Returns:
        적절한 HTTP 응답
    """
    # 요청 정보 로깅
    logger.error(
        f"ComixServerException 발생: {exc.message} "
        f"(상태코드: {exc.status_code}) "
        f"요청: {request.method} {request.url}"
    )
    
    # 디버그 모드에서는 상세 정보 포함
    from app.models.config import settings
    
    if settings.debug_mode:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method
            }
        )
    else:
        # 프로덕션 모드에서는 간단한 텍스트 응답
        return PlainTextResponse(
            content=exc.detail,
            status_code=exc.status_code
        )


async def http_exception_handler(
    request: Request, 
    exc: HTTPException
) -> Union[JSONResponse, PlainTextResponse]:
    """
    FastAPI HTTPException 핸들러
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 HTTPException
        
    Returns:
        적절한 HTTP 응답
    """
    # 요청 정보 로깅
    logger.warning(
        f"HTTPException 발생: {exc.detail} "
        f"(상태코드: {exc.status_code}) "
        f"요청: {request.method} {request.url}"
    )
    
    from app.models.config import settings
    
    if settings.debug_mode:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Exception",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method
            }
        )
    else:
        return PlainTextResponse(
            content=str(exc.detail),
            status_code=exc.status_code
        )


async def starlette_http_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> Union[JSONResponse, PlainTextResponse]:
    """
    Starlette HTTPException 핸들러
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 StarletteHTTPException
        
    Returns:
        적절한 HTTP 응답
    """
    # 요청 정보 로깅
    logger.warning(
        f"StarletteHTTPException 발생: {exc.detail} "
        f"(상태코드: {exc.status_code}) "
        f"요청: {request.method} {request.url}"
    )
    
    from app.models.config import settings
    
    if settings.debug_mode:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Starlette HTTP Exception",
                "detail": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path),
                "method": request.method
            }
        )
    else:
        return PlainTextResponse(
            content=str(exc.detail),
            status_code=exc.status_code
        )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> Union[JSONResponse, PlainTextResponse]:
    """
    일반 예외 핸들러 (예상하지 못한 모든 예외)
    
    Args:
        request: FastAPI 요청 객체
        exc: 발생한 Exception
        
    Returns:
        적절한 HTTP 응답
    """
    # 상세한 오류 정보 로깅
    logger.error(
        f"예상하지 못한 예외 발생: {str(exc)} "
        f"요청: {request.method} {request.url} "
        f"스택 트레이스: {traceback.format_exc()}"
    )
    
    from app.models.config import settings
    
    if settings.debug_mode:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "status_code": 500,
                "path": str(request.url.path),
                "method": request.method,
                "traceback": traceback.format_exc().split('\n')
            }
        )
    else:
        return PlainTextResponse(
            content="서버 내부 오류가 발생했습니다",
            status_code=500
        )


def register_exception_handlers(app):
    """
    FastAPI 앱에 예외 핸들러들을 등록합니다
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    app.add_exception_handler(ComixServerException, comix_server_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("예외 핸들러 등록 완료")