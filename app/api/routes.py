"""FastAPI 라우터 및 엔드포인트 정의"""

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