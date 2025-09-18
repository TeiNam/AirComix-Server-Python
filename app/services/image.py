"""이미지 스트리밍 서비스 모듈

이 모듈은 이미지 파일의 스트리밍, MIME 타입 감지, 그리고 아카이브에서 이미지 추출 기능을 제공합니다.
"""

import mimetypes
from pathlib import Path
from typing import Optional, AsyncGenerator

import aiofiles
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.models.config import Settings
from app.services.archive import ArchiveService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ImageService:
    """이미지 파일 처리 및 스트리밍을 담당하는 서비스 클래스"""
    
    def __init__(self, settings: Settings, archive_service: ArchiveService):
        self.settings = settings
        self.archive_service = archive_service
        
        # MIME 타입 매핑 초기화
        self._init_mime_types()
    
    def _init_mime_types(self) -> None:
        """MIME 타입 매핑을 초기화합니다"""
        # 기본 MIME 타입들을 추가
        mimetypes.add_type('image/jpeg', '.jpg')
        mimetypes.add_type('image/jpeg', '.jpeg')
        mimetypes.add_type('image/png', '.png')
        mimetypes.add_type('image/gif', '.gif')
        mimetypes.add_type('image/tiff', '.tif')
        mimetypes.add_type('image/tiff', '.tiff')
        mimetypes.add_type('image/bmp', '.bmp')
    
    def get_mime_type(self, filename: str) -> str:
        """파일 확장자로부터 MIME 타입을 결정합니다
        
        Args:
            filename: 파일명
            
        Returns:
            MIME 타입 문자열 (기본값: 'application/octet-stream')
        """
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type.startswith('image/'):
            return mime_type
        
        # 확장자 기반 fallback
        ext = Path(filename).suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.tif': 'image/tiff',
            '.tiff': 'image/tiff',
            '.bmp': 'image/bmp'
        }
        
        return mime_map.get(ext, 'application/octet-stream')
    
    def is_image_file(self, filename: str) -> bool:
        """파일이 지원되는 이미지 파일인지 확인합니다
        
        Args:
            filename: 파일명
            
        Returns:
            이미지 파일 여부
        """
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in [ext.lower() for ext in self.settings.image_extensions]
    
    async def _file_streamer(self, file_path: Path, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """파일을 청크 단위로 스트리밍합니다
        
        Args:
            file_path: 스트리밍할 파일 경로
            chunk_size: 청크 크기 (바이트)
            
        Yields:
            파일 데이터 청크
        """
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                while chunk := await file.read(chunk_size):
                    yield chunk
        except Exception as e:
            logger.error(f"파일 스트리밍 중 오류 발생: {file_path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="파일 스트리밍 오류")
    
    async def stream_image(self, image_path: Path) -> StreamingResponse:
        """직접 이미지 파일을 스트리밍합니다
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            StreamingResponse 객체
            
        Raises:
            HTTPException: 파일이 존재하지 않거나 접근할 수 없는 경우
        """
        if not image_path.exists():
            logger.warning(f"이미지 파일을 찾을 수 없음: {image_path}")
            raise HTTPException(status_code=404, detail="이미지 파일을 찾을 수 없습니다")
        
        if not image_path.is_file():
            logger.warning(f"경로가 파일이 아님: {image_path}")
            raise HTTPException(status_code=404, detail="유효한 이미지 파일이 아닙니다")
        
        try:
            # 파일 크기 확인
            file_size = image_path.stat().st_size
            mime_type = self.get_mime_type(image_path.name)
            
            logger.info(f"이미지 스트리밍 시작: {image_path.name}, 크기: {file_size}, MIME: {mime_type}")
            
            headers = {
                'Content-Type': mime_type,
                'Content-Length': str(file_size),
                'Accept-Ranges': 'bytes'
            }
            
            return StreamingResponse(
                self._file_streamer(image_path),
                media_type=mime_type,
                headers=headers
            )
            
        except Exception as e:
            logger.error(f"이미지 스트리밍 준비 중 오류: {image_path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="이미지 스트리밍 오류")
    
    async def _archive_streamer(self, archive_path: Path, image_path: str, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
        """아카이브에서 이미지를 추출하여 스트리밍합니다
        
        Args:
            archive_path: 아카이브 파일 경로
            image_path: 아카이브 내 이미지 경로
            chunk_size: 청크 크기 (바이트)
            
        Yields:
            이미지 데이터 청크
        """
        try:
            # 아카이브에서 파일 데이터를 한 번에 추출
            image_data = await self.archive_service.extract_file_from_archive(archive_path, image_path)
            
            # 데이터를 청크 단위로 yield
            for i in range(0, len(image_data), chunk_size):
                yield image_data[i:i + chunk_size]
                
        except Exception as e:
            logger.error(f"아카이브에서 이미지 스트리밍 중 오류: {archive_path}:{image_path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="아카이브 이미지 스트리밍 오류")
    
    async def stream_image_from_archive(self, archive_path: Path, image_path: str) -> StreamingResponse:
        """아카이브에서 이미지를 스트리밍합니다
        
        Args:
            archive_path: 아카이브 파일 경로
            image_path: 아카이브 내 이미지 경로
            
        Returns:
            StreamingResponse 객체
            
        Raises:
            HTTPException: 아카이브나 이미지를 찾을 수 없는 경우
        """
        if not archive_path.exists():
            logger.warning(f"아카이브 파일을 찾을 수 없음: {archive_path}")
            raise HTTPException(status_code=404, detail="아카이브 파일을 찾을 수 없습니다")
        
        try:
            # 아카이브 내 파일 목록 확인
            archive_contents = await self.archive_service.list_archive_contents(archive_path)
            
            if image_path not in archive_contents:
                logger.warning(f"아카이브 내 이미지를 찾을 수 없음: {archive_path}:{image_path}")
                raise HTTPException(status_code=404, detail="아카이브 내 이미지를 찾을 수 없습니다")
            
            # 이미지 파일인지 확인
            if not self.is_image_file(image_path):
                logger.warning(f"지원되지 않는 이미지 형식: {image_path}")
                raise HTTPException(status_code=400, detail="지원되지 않는 이미지 형식입니다")
            
            mime_type = self.get_mime_type(image_path)
            
            logger.info(f"아카이브에서 이미지 스트리밍 시작: {archive_path.name}:{image_path}, MIME: {mime_type}")
            
            headers = {
                'Content-Type': mime_type,
                'Accept-Ranges': 'bytes'
            }
            
            return StreamingResponse(
                self._archive_streamer(archive_path, image_path),
                media_type=mime_type,
                headers=headers
            )
            
        except HTTPException:
            # HTTPException은 그대로 재발생
            raise
        except Exception as e:
            logger.error(f"아카이브 이미지 스트리밍 준비 중 오류: {archive_path}:{image_path}, 오류: {e}")
            raise HTTPException(status_code=500, detail="아카이브 이미지 스트리밍 오류")
    
    async def get_image_info(self, image_path: Path) -> Optional[dict]:
        """이미지 파일의 기본 정보를 반환합니다
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            이미지 정보 딕셔너리 또는 None
        """
        if not image_path.exists() or not image_path.is_file():
            return None
        
        try:
            stat = image_path.stat()
            return {
                'name': image_path.name,
                'size': stat.st_size,
                'mime_type': self.get_mime_type(image_path.name),
                'is_image': self.is_image_file(image_path.name)
            }
        except Exception as e:
            logger.error(f"이미지 정보 조회 중 오류: {image_path}, 오류: {e}")
            return None