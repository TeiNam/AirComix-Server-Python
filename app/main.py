"""
Comix Server 메인 애플리케이션

FastAPI 애플리케이션 생성 및 설정
"""

# .env 파일 로드 (다른 import보다 먼저)
from dotenv import load_dotenv
load_dotenv()

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin_router, router
from app.models.config import settings
from app.utils.logging import get_logger, setup_logging
from app.exception_handlers import register_exception_handlers
from app.services import FileWatcherService, ThumbnailService, ArchiveService
from app.middleware import BasicAuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """애플리케이션 생명주기 관리"""
    logger = get_logger(__name__)
    
    # 시작 시 초기화
    logger.info("Comix Server 시작 중...")
    logger.info(f"Manga 디렉토리: {settings.manga_directory}")
    logger.info(f"서버 포트: {settings.server_port}")
    logger.info(f"디버그 모드: {settings.debug_mode}")
    
    # 파일 감시 서비스 시작
    archive_service = ArchiveService()
    thumbnail_service = ThumbnailService(archive_service)
    file_watcher = FileWatcherService(thumbnail_service)
    
    await file_watcher.start_watching()
    logger.info("파일 시스템 감시 서비스 시작됨")
    
    # 애플리케이션에 서비스 저장 (나중에 접근 가능하도록)
    app.state.file_watcher = file_watcher
    app.state.thumbnail_service = thumbnail_service
    
    yield
    
    # 종료 시 정리
    logger.info("Comix Server 종료 중...")
    await file_watcher.stop_watching()
    logger.info("파일 시스템 감시 서비스 중지됨")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성 및 설정"""
    
    # 로깅 설정
    setup_logging()
    logger = get_logger(__name__)
    
    # FastAPI 앱 생성
    # API 문서는 디버그 모드에서만 노출한다 (프로덕션에서 엔드포인트 목록 노출 방지)
    app = FastAPI(
        title="Comix Server",
        description="Python port of comix-server for streaming comic books to AirComix iOS app",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug_mode,
        docs_url="/docs" if settings.debug_mode else None,
        redoc_url="/redoc" if settings.debug_mode else None,
        openapi_url="/openapi.json" if settings.debug_mode else None,
    )
    
    # 인증 미들웨어 설정
    if settings.enable_auth:
        app.add_middleware(BasicAuthMiddleware)
        logger.info("Basic Auth 미들웨어 활성화됨 (.htaccess 방식)")
        logger.info("패스워드 인증 활성화됨")
    
    # CORS 미들웨어 설정 (디버그 모드에서만)
    # allow_origins=["*"] 와 allow_credentials=True 조합은 브라우저가 거부하는 무효 조합이므로
    # 자격증명 전송은 허용하지 않는다 (AirComix 앱은 CORS 대상이 아니라 영향 없음)
    if settings.debug_mode:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS 미들웨어 활성화됨 (디버그 모드)")

    # 라우터 포함
    app.include_router(router)

    # 관리용 엔드포인트는 보호 수단이 있을 때만 노출한다.
    # 인증이 꺼져 있으면 캐시 삭제 같은 파괴적 작업이 무인증으로 열리므로 등록하지 않는다.
    if settings.enable_auth:
        app.include_router(admin_router)
        logger.info("관리 엔드포인트 활성화됨 (/admin/*)")
    else:
        logger.info("인증이 비활성화되어 관리 엔드포인트를 등록하지 않음")
    
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