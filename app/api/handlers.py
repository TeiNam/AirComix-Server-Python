"""만화 요청 처리 핸들러 모듈

이 모듈은 만화 관련 요청을 처리하는 핸들러 클래스들을 제공합니다.
"""

from pathlib import Path
from typing import Union
from urllib.parse import unquote

from fastapi import HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.models.config import Settings
from app.services import FileSystemService, ArchiveService, ImageService
from app.utils.logging import get_logger
from app.utils.path import PathUtils
from app.exceptions import (
    FileNotFoundError, AccessDeniedError, UnsupportedFileTypeError,
    PathTraversalError, ArchiveError, ImageProcessingError
)

logger = get_logger(__name__)


class MangaRequestHandler:
    """만화 요청을 처리하는 메인 핸들러 클래스"""
    
    def __init__(
        self,
        settings: Settings,
        filesystem_service: FileSystemService,
        archive_service: ArchiveService,
        image_service: ImageService
    ):
        self.settings = settings
        self.filesystem_service = filesystem_service
        self.archive_service = archive_service
        self.image_service = image_service
        self.manga_root = Path(settings.manga_directory)
    
    async def handle_request(self, path: str) -> Union[PlainTextResponse, StreamingResponse]:
        """메인 요청 디스패처 - 경로 타입에 따라 적절한 핸들러로 라우팅
        
        Args:
            path: 요청된 경로 (URL 인코딩된 상태)
            
        Returns:
            적절한 응답 객체
            
        Raises:
            HTTPException: 경로가 유효하지 않거나 접근할 수 없는 경우
        """
        try:
            # URL 디코딩
            decoded_path = unquote(path)
            logger.info(f"만화 요청 처리 시작: {decoded_path}")
            
            # 경로 검증 및 정규화
            normalized_path = self._validate_and_normalize_path(decoded_path)
            full_path = self.manga_root / normalized_path
            
            # 경로 타입에 따른 처리 분기
            if self._is_archive_image_request(decoded_path):
                # 아카이브 내 이미지 요청
                return await self._handle_archive_image_request(decoded_path)
            elif full_path.is_file():
                if self.archive_service.is_archive_file(full_path.name):
                    # 아카이브 파일 목록 요청
                    return await self.handle_archive_listing(full_path)
                elif self.image_service.is_image_file(full_path.name):
                    # 직접 이미지 파일 요청
                    return await self._handle_direct_image_request(full_path)
                else:
                    logger.warning(f"지원되지 않는 파일 형식: {full_path}")
                    raise UnsupportedFileTypeError(str(full_path))
            elif full_path.is_dir():
                # 디렉토리 목록 요청
                return await self.handle_directory_listing(full_path)
            else:
                logger.warning(f"파일 또는 디렉토리를 찾을 수 없음: {full_path}")
                raise FileNotFoundError(str(full_path))
                
        except (FileNotFoundError, AccessDeniedError, UnsupportedFileTypeError, 
                PathTraversalError, ArchiveError, ImageProcessingError) as e:
            # 커스텀 예외는 그대로 재발생 (예외 핸들러에서 처리됨)
            raise e
        except HTTPException:
            # HTTPException은 그대로 재발생
            raise
        except Exception as e:
            logger.error(f"만화 요청 처리 중 오류: {path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="서버 내부 오류")
    
    def _validate_and_normalize_path(self, path: str) -> str:
        """경로를 검증하고 정규화합니다
        
        Args:
            path: 검증할 경로
            
        Returns:
            정규화된 경로
            
        Raises:
            HTTPException: 경로가 안전하지 않은 경우
        """
        # 빈 경로 처리
        if not path or path == "/":
            return ""
        
        # 앞의 슬래시 제거
        if path.startswith("/"):
            path = path[1:]
        
        # 경로 안전성 검증
        if not PathUtils.is_safe_path(self.manga_root, path):
            logger.warning(f"안전하지 않은 경로 접근 시도: {path}")
            raise PathTraversalError(path)
        
        # 경로 정규화
        return PathUtils.normalize_path(path)
    
    def _is_archive_image_request(self, path: str) -> bool:
        """아카이브 내 이미지 요청인지 확인합니다
        
        Args:
            path: 확인할 경로
            
        Returns:
            아카이브 내 이미지 요청 여부
        """
        try:
            archive_path, image_path = PathUtils.extract_archive_and_image_paths(path)
            return bool(archive_path and image_path)
        except:
            return False
    
    async def _handle_archive_image_request(self, path: str) -> StreamingResponse:
        """아카이브 내 이미지 요청을 처리합니다
        
        Args:
            path: 아카이브 내 이미지 경로
            
        Returns:
            이미지 스트리밍 응답
        """
        try:
            archive_path, image_path = PathUtils.extract_archive_and_image_paths(path)
            full_archive_path = self.manga_root / archive_path
            
            logger.info(f"아카이브 이미지 요청: {archive_path} -> {image_path}")
            
            return await self.image_service.stream_image_from_archive(
                full_archive_path, image_path
            )
            
        except Exception as e:
            logger.error(f"아카이브 이미지 요청 처리 중 오류: {path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="아카이브 이미지 처리 오류")
    
    async def _handle_direct_image_request(self, image_path: Path) -> StreamingResponse:
        """직접 이미지 파일 요청을 처리합니다
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            이미지 스트리밍 응답
        """
        logger.info(f"직접 이미지 요청: {image_path.name}")
        return await self.image_service.stream_image(image_path)
    
    async def handle_directory_listing(self, directory_path: Path) -> PlainTextResponse:
        """디렉토리 목록 요청을 처리합니다
        
        Args:
            directory_path: 디렉토리 경로
            
        Returns:
            디렉토리 내용 목록 (줄바꿈으로 구분)
        """
        try:
            logger.info(f"디렉토리 목록 요청: {directory_path}")
            
            # 절대 경로를 상대 경로로 변환
            try:
                relative_path = directory_path.relative_to(self.manga_root)
                relative_path_str = str(relative_path) if str(relative_path) != "." else ""
            except ValueError:
                # directory_path가 manga_root 외부에 있는 경우
                logger.warning(f"manga_root 외부 경로 접근 시도: {directory_path}")
                raise AccessDeniedError(str(directory_path))
            
            # 디렉토리 목록 조회
            file_list = await self.filesystem_service.list_directory(relative_path_str)
            
            # 줄바꿈으로 구분된 문자열로 변환
            content = "\n".join(file_list)
            
            logger.info(f"디렉토리 목록 반환: {len(file_list)}개 항목")
            return PlainTextResponse(content=content)
            
        except Exception as e:
            logger.error(f"디렉토리 목록 조회 중 오류: {directory_path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="디렉토리 목록 조회 오류")
    
    async def handle_archive_listing(self, archive_path: Path) -> PlainTextResponse:
        """아카이브 파일 목록 요청을 처리합니다
        
        Args:
            archive_path: 아카이브 파일 경로
            
        Returns:
            아카이브 내 이미지 목록 (줄바꿈으로 구분)
        """
        try:
            logger.info(f"아카이브 목록 요청: {archive_path.name}")
            
            # 아카이브 내용 목록 조회
            image_list = await self.archive_service.list_archive_contents(archive_path)
            
            # 줄바꿈으로 구분된 문자열로 변환
            content = "\n".join(image_list)
            
            logger.info(f"아카이브 목록 반환: {len(image_list)}개 이미지")
            return PlainTextResponse(content=content)
            
        except Exception as e:
            logger.error(f"아카이브 목록 조회 중 오류: {archive_path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="아카이브 목록 조회 오류")