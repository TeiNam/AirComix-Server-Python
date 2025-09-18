"""
로깅 설정 및 유틸리티

구조화된 로깅과 일관된 포맷팅을 제공
"""

import logging
import sys
from typing import Optional

from app.models.config import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """로깅 설정 초기화"""
    level = log_level or settings.log_level
    
    # 로그 포맷 설정
    if settings.debug_mode:
        # 디버그 모드에서는 상세한 정보 포함
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    else:
        # 프로덕션 모드에서는 간단한 포맷
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
    
    # 로깅 설정
    logging.basicConfig(
        level=getattr(logging, level),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,  # 기존 설정 덮어쓰기
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    if not settings.debug_mode:
        logging.getLogger("uvicorn").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, method: str, path: str, status_code: int) -> None:
    """HTTP 요청 로깅"""
    logger.info(f"{method} {path} - {status_code}")


def log_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """에러 로깅"""
    if context:
        logger.error(f"{context}: {str(error)}", exc_info=settings.debug_mode)
    else:
        logger.error(str(error), exc_info=settings.debug_mode)


def log_performance(logger: logging.Logger, operation: str, duration: float) -> None:
    """성능 로깅"""
    logger.info(f"Performance - {operation}: {duration:.3f}s")