"""
Comix Server 메인 애플리케이션

FastAPI 애플리케이션 생성 및 설정
"""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.models.config import settings
from app.utils.logging import get_logger, setup_logging
from app.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 생명주기 관리"""
    logger = get_logger(__name__)
    
    # 시작 시 초기화
    logger.info("Comix Server 시작 중...")
    logger.info(f"Manga 디렉토리: {settings.manga_directory}")
    logger.info(f"서버 포트: {settings.server_port}")
    logger.info(f"디버그 모드: {settings.debug_mode}")
    
    yield
    
    # 종료 시 정리
    logger.info("Comix Server 종료 중...")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성 및 설정"""
    
    # 로깅 설정
    setup_logging()
    logger = get_logger(__name__)
    
    # FastAPI 앱 생성
    app = FastAPI(
        title="Comix Server",
        description="Python port of comix-server for streaming comic books to AirComix iOS app",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug_mode,
    )
    
    # CORS 미들웨어 설정 (디버그 모드에서만)
    if settings.debug_mode:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS 미들웨어 활성화됨 (디버그 모드)")
    
    # 라우터 포함
    app.include_router(router)
    
    # 예외 핸들러 등록
    register_exception_handlers(app)
    
    logger.info("FastAPI 애플리케이션 생성 완료")
    return app


def main() -> None:
    """메인 엔트리 포인트"""
    import uvicorn
    
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Comix Server 시작: {settings.server_host}:{settings.server_port}")
        uvicorn.run(
            "app.main:create_app",
            factory=True,
            host=settings.server_host,
            port=settings.server_port,
            reload=settings.debug_mode,
            log_level=settings.log_level.lower(),
        )
    except KeyboardInterrupt:
        logger.info("사용자에 의해 서버가 중단되었습니다")
        sys.exit(0)
    except Exception as e:
        logger.error(f"서버 시작 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()