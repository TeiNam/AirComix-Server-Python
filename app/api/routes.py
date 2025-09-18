"""FastAPI 라우터 및 엔드포인트 정의"""

import io
from pathlib import Path
from typing import Union
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.api.handlers import MangaRequestHandler
from app.models.config import settings
from app.services import FileSystemService, ArchiveService, ImageService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 서비스 인스턴스들 생성
filesystem_service = FileSystemService(Path(settings.manga_directory))
archive_service = ArchiveService()
image_service = ImageService(settings, archive_service)

# 썸네일 서비스 추가
from app.services.thumbnail import ThumbnailService
thumbnail_service = ThumbnailService(archive_service)

# 만화 요청 핸들러 생성
manga_handler = MangaRequestHandler(
    settings=settings,
    filesystem_service=filesystem_service,
    archive_service=archive_service,
    image_service=image_service
)


@router.get("/", response_class=PlainTextResponse)
async def get_root_directory_name():
    """루트 엔드포인트 - 만화 디렉토리 이름을 반환합니다
    
    AirComix 앱이 서버에 연결할 때 가장 먼저 호출하는 엔드포인트입니다.
    만화 컬렉션의 루트 디렉토리 이름을 반환합니다.
    
    Returns:
        만화 디렉토리의 이름 (문자열)
    """
    try:
        manga_dir = Path(settings.manga_directory)
        directory_name = manga_dir.name if manga_dir.name else "manga"
        
        logger.info(f"루트 디렉토리 이름 요청: {directory_name}")
        return directory_name
        
    except Exception as e:
        logger.error(f"루트 디렉토리 이름 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류")


@router.get("/welcome.102", response_class=PlainTextResponse)
async def get_server_info():
    """서버 정보 엔드포인트 - 서버 기능 정보를 반환합니다
    
    AirComix 앱이 서버의 기능을 확인하기 위해 호출하는 엔드포인트입니다.
    서버가 지원하는 기능들을 텍스트 형태로 반환합니다.
    
    Returns:
        서버 기능 정보 (텍스트)
    """
    try:
        server_info = (
            "allowDownload=True\n"
            "allowImageProcess=True\n"
            "Comix Server Python Port - FastAPI 기반 만화 스트리밍 서버"
        )
        
        logger.info("서버 정보 요청")
        return server_info
        
    except Exception as e:
        logger.error(f"서버 정보 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail="서버 오류")


@router.get("/health", response_class=PlainTextResponse)
async def health_check():
    """헬스 체크 엔드포인트
    
    서버의 상태를 확인하기 위한 엔드포인트입니다.
    로드 밸런서나 모니터링 시스템에서 사용됩니다.
    
    Returns:
        서버 상태 정보
    """
    try:
        # 기본 서버 상태 확인
        manga_dir = Path(settings.manga_directory)
        
        # 만화 디렉토리 접근 가능 여부 확인
        if not manga_dir.exists():
            raise HTTPException(status_code=503, detail="Manga directory not accessible")
        
        # 간단한 상태 정보 반환
        status_info = (
            "status=healthy\n"
            f"manga_directory={settings.manga_directory}\n"
            f"debug_mode={settings.debug_mode}\n"
            "service=comix-server"
        )
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"헬스 체크 중 오류: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/thumbnail/{path:path}")
async def get_thumbnail(path: str):
    """썸네일 요청 처리 엔드포인트
    
    아카이브 파일이나 폴더의 썸네일을 반환합니다.
    - 아카이브 파일: 첫 번째 이미지의 썸네일
    - 폴더: 첫 번째 아카이브의 첫 번째 이미지 썸네일
    - manga 루트 폴더: aircomix.png 썸네일
    
    Args:
        path: 썸네일을 요청할 경로
        
    Returns:
        JPEG 형식의 썸네일 이미지
    """
    try:
        from urllib.parse import unquote
        from app.utils.path import PathUtils
        
        # URL 디코딩
        decoded_path = unquote(path)
        logger.debug(f"썸네일 요청: {decoded_path}")
        
        # 경로 검증 및 정규화
        manga_root = Path(settings.manga_directory)
        target_path = PathUtils.resolve_safe_path(manga_root, decoded_path)
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="파일 또는 폴더를 찾을 수 없습니다")
        
        # 썸네일 생성 또는 조회
        thumbnail_data = await thumbnail_service.get_or_create_thumbnail(target_path)
        
        if not thumbnail_data:
            raise HTTPException(status_code=404, detail="썸네일을 생성할 수 없습니다")
        
        # JPEG 이미지로 응답
        return StreamingResponse(
            io.BytesIO(thumbnail_data),
            media_type="image/jpeg",
            headers={
                "Content-Length": str(len(thumbnail_data)),
                "Cache-Control": "public, max-age=3600"  # 1시간 캐시
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"썸네일 처리 중 오류: {path}, {e}")
        raise HTTPException(status_code=500, detail="썸네일 처리 실패")


@router.get("/admin/thumbnail/info")
async def get_thumbnail_cache_info():
    """썸네일 캐시 정보 조회 엔드포인트
    
    현재 썸네일 캐시의 상태 정보를 반환합니다.
    
    Returns:
        썸네일 캐시 정보 (JSON)
    """
    try:
        cache_info = await thumbnail_service.get_cache_info()
        return cache_info
    except Exception as e:
        logger.error(f"썸네일 캐시 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="캐시 정보 조회 실패")


@router.post("/admin/thumbnail/cleanup")
async def cleanup_thumbnail_cache():
    """고아 썸네일 정리 엔드포인트
    
    원본 파일이 삭제된 썸네일들을 정리합니다.
    
    Returns:
        정리 결과 정보
    """
    try:
        deleted_count = await thumbnail_service.cleanup_orphaned_thumbnails()
        return {
            "message": "썸네일 정리 완료",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"썸네일 정리 실패: {e}")
        raise HTTPException(status_code=500, detail="썸네일 정리 실패")


@router.delete("/admin/thumbnail/cache")
async def clear_thumbnail_cache():
    """썸네일 캐시 전체 삭제 엔드포인트
    
    모든 썸네일 캐시를 삭제합니다.
    
    Returns:
        삭제 결과 정보
    """
    try:
        await thumbnail_service.clear_cache()
        return {"message": "썸네일 캐시 삭제 완료"}
    except Exception as e:
        logger.error(f"썸네일 캐시 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail="썸네일 캐시 삭제 실패")


@router.get("/{path}.thm")
async def get_thumbnail_by_thm_extension(path: str):
    """AirComix 앱 호환 썸네일 엔드포인트 (.thm 확장자)
    
    AirComix 앱이 사용하는 .thm 확장자 썸네일 요청을 처리합니다.
    
    Args:
        path: 썸네일을 요청할 경로 (확장자 제외)
        
    Returns:
        JPEG 형식의 썸네일 이미지
    """
    try:
        from urllib.parse import unquote
        from app.utils.path import PathUtils
        
        # URL 디코딩
        decoded_path = unquote(path)
        logger.debug(f"썸네일 요청 (.thm): {decoded_path}")
        
        # 경로 검증 및 정규화
        manga_root = Path(settings.manga_directory)
        
        # 빈 경로이거나 "manga"인 경우 루트 폴더 썸네일
        if not decoded_path or decoded_path == "manga":
            target_path = manga_root
        else:
            target_path = PathUtils.resolve_safe_path(manga_root, decoded_path)
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="파일 또는 폴더를 찾을 수 없습니다")
        
        # 썸네일 생성 또는 조회
        thumbnail_data = await thumbnail_service.get_or_create_thumbnail(target_path)
        
        if not thumbnail_data:
            raise HTTPException(status_code=404, detail="썸네일을 생성할 수 없습니다")
        
        # JPEG 이미지로 응답
        return StreamingResponse(
            io.BytesIO(thumbnail_data),
            media_type="image/jpeg",
            headers={
                "Content-Length": str(len(thumbnail_data)),
                "Cache-Control": "public, max-age=3600"  # 1시간 캐시
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"썸네일 처리 중 오류 (.thm): {path}, {e}")
        raise HTTPException(status_code=500, detail="썸네일 처리 실패")


@router.get("/manga/{path:path}", response_model=None)
async def handle_manga_request(path: str):
    """만화 요청 처리 엔드포인트
    
    만화 디렉토리 내의 파일이나 디렉토리에 대한 모든 요청을 처리합니다.
    요청 타입에 따라 다음과 같이 동작합니다:
    
    - 디렉토리: 파일 목록을 줄바꿈으로 구분하여 반환
    - 아카이브 파일: 내부 이미지 목록을 줄바꿈으로 구분하여 반환  
    - 이미지 파일: 이미지를 스트리밍으로 반환
    - 아카이브 내 이미지: 아카이브에서 이미지를 추출하여 스트리밍으로 반환
    
    Args:
        path: 요청된 경로 (URL 인코딩된 상태)
        
    Returns:
        요청 타입에 따른 적절한 응답
    """
    return await manga_handler.handle_request(path)