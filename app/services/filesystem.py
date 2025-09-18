"""
파일 시스템 서비스

디렉토리 목록 조회, 파일 타입 감지, 메타데이터 추출 등을 담당
"""

import asyncio
from pathlib import Path
from typing import List, Optional
import mimetypes
import aiofiles.os

from app.models.config import settings
from app.models.data import FileInfo
from app.utils.logging import get_logger
from app.utils.path import PathUtils

logger = get_logger(__name__)


class FileSystemService:
    """파일 시스템 서비스 클래스"""
    
    def __init__(self, manga_root: Optional[Path] = None):
        """
        FileSystemService 초기화
        
        Args:
            manga_root: 만화 루트 디렉토리 (None이면 설정에서 가져옴)
        """
        if manga_root is not None:
            self.manga_root = Path(manga_root)
        else:
            self.manga_root = Path(settings.manga_directory)
        logger.debug(f"FileSystemService 초기화: {self.manga_root}")
    
    async def list_directory(self, path: str) -> List[str]:
        """
        디렉토리 내용 목록 조회 (필터링 적용)
        
        Args:
            path: 조회할 디렉토리 경로 (manga_root 기준 상대 경로)
            
        Returns:
            List[str]: 필터링된 파일 및 디렉토리 목록
        """
        try:
            # 경로 안전성 검사
            if not PathUtils.is_safe_path(self.manga_root, path):
                logger.warning(f"안전하지 않은 경로 접근 시도: {path}")
                return []
            
            # 실제 디렉토리 경로 구성
            normalized_path = PathUtils.normalize_path(path)
            if normalized_path:
                full_path = self.manga_root / normalized_path
            else:
                full_path = self.manga_root
            
            logger.debug(f"디렉토리 목록 조회: {full_path}")
            
            # 디렉토리 존재 확인
            if not await aiofiles.os.path.exists(full_path):
                logger.warning(f"디렉토리가 존재하지 않음: {full_path}")
                return []
            
            if not await aiofiles.os.path.isdir(full_path):
                logger.warning(f"디렉토리가 아님: {full_path}")
                return []
            
            # 디렉토리 내용 읽기
            try:
                entries = await aiofiles.os.listdir(full_path)
            except PermissionError:
                logger.error(f"디렉토리 접근 권한 없음: {full_path}")
                return []
            except Exception as e:
                logger.error(f"디렉토리 읽기 실패: {full_path}, 오류: {e}")
                return []
            
            # 필터링된 목록 생성
            filtered_entries = []
            for entry in entries:
                if await self._is_entry_supported(full_path / entry, entry):
                    filtered_entries.append(entry)
            
            # 정렬 (디렉토리 먼저, 그 다음 파일명 순)
            filtered_entries.sort(key=lambda x: (not Path(full_path / x).is_dir(), x.lower()))
            
            logger.debug(f"필터링된 항목 수: {len(filtered_entries)}")
            return filtered_entries
            
        except Exception as e:
            logger.error(f"디렉토리 목록 조회 실패: {path}, 오류: {e}")
            return []
    
    async def _is_entry_supported(self, entry_path: Path, entry_name: str) -> bool:
        """
        디렉토리 엔트리가 지원되는지 확인
        
        Args:
            entry_path: 엔트리의 전체 경로
            entry_name: 엔트리 이름
            
        Returns:
            bool: 지원되는 엔트리인지 여부
        """
        # 숨김 파일 체크
        if settings.is_hidden_file(entry_name):
            return False
        
        try:
            # 디렉토리인 경우 허용
            if await aiofiles.os.path.isdir(entry_path):
                return True
            
            # 파일인 경우 지원되는 형식인지 확인
            if await aiofiles.os.path.isfile(entry_path):
                return settings.is_supported_file(entry_name)
            
            # 심볼릭 링크나 기타 특수 파일은 제외
            return False
            
        except Exception as e:
            logger.debug(f"엔트리 지원 여부 확인 실패: {entry_name}, 오류: {e}")
            return False
    
    async def is_supported_file(self, filename: str) -> bool:
        """
        파일이 지원되는 형식인지 확인
        
        Args:
            filename: 확인할 파일명
            
        Returns:
            bool: 지원되는 파일인지 여부
        """
        return settings.is_supported_file(filename)
    
    async def get_file_info(self, path: str) -> Optional[FileInfo]:
        """
        파일 정보 조회
        
        Args:
            path: 파일 경로 (manga_root 기준 상대 경로)
            
        Returns:
            Optional[FileInfo]: 파일 정보 (없으면 None)
        """
        try:
            # 경로 안전성 검사
            if not PathUtils.is_safe_path(self.manga_root, path):
                logger.warning(f"안전하지 않은 경로 접근 시도: {path}")
                return None
            
            # 실제 파일 경로 구성
            normalized_path = PathUtils.normalize_path(path)
            if normalized_path:
                full_path = self.manga_root / normalized_path
            else:
                full_path = self.manga_root
            
            # 파일 존재 확인
            if not await aiofiles.os.path.exists(full_path):
                return None
            
            # 파일 정보 수집
            filename = PathUtils.get_filename(path) or full_path.name
            is_directory = await aiofiles.os.path.isdir(full_path)
            is_archive = False
            is_image = False
            size = None
            mime_type = None
            
            if not is_directory:
                # 파일 크기 조회
                try:
                    stat_result = await aiofiles.os.stat(full_path)
                    size = stat_result.st_size
                except Exception as e:
                    logger.debug(f"파일 크기 조회 실패: {full_path}, 오류: {e}")
                
                # 파일 타입 확인
                is_archive = settings.is_archive_file(filename)
                is_image = settings.is_image_file(filename)
                
                # MIME 타입 확인
                if is_image:
                    mime_type = self._get_mime_type(filename)
            
            return FileInfo(
                name=filename,
                path=full_path,
                is_directory=is_directory,
                is_archive=is_archive,
                is_image=is_image,
                size=size,
                mime_type=mime_type
            )
            
        except Exception as e:
            logger.error(f"파일 정보 조회 실패: {path}, 오류: {e}")
            return None
    
    def _get_mime_type(self, filename: str) -> str:
        """
        파일명으로부터 MIME 타입 추출
        
        Args:
            filename: 파일명
            
        Returns:
            str: MIME 타입
        """
        # mimetypes 모듈 사용
        mime_type, _ = mimetypes.guess_type(filename)
        
        if mime_type:
            return mime_type
        
        # 확장자 기반 매핑
        ext = PathUtils.get_file_extension(filename)
        mime_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'tif': 'image/tiff',
            'tiff': 'image/tiff',
        }
        
        return mime_map.get(ext, 'application/octet-stream')
    
    async def file_exists(self, path: str) -> bool:
        """
        파일 존재 여부 확인
        
        Args:
            path: 확인할 파일 경로
            
        Returns:
            bool: 파일 존재 여부
        """
        try:
            if not PathUtils.is_safe_path(self.manga_root, path):
                return False
            
            normalized_path = PathUtils.normalize_path(path)
            if normalized_path:
                full_path = self.manga_root / normalized_path
            else:
                full_path = self.manga_root
            
            return await aiofiles.os.path.exists(full_path)
            
        except Exception as e:
            logger.debug(f"파일 존재 확인 실패: {path}, 오류: {e}")
            return False
    
    async def is_directory(self, path: str) -> bool:
        """
        디렉토리 여부 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            bool: 디렉토리 여부
        """
        try:
            if not PathUtils.is_safe_path(self.manga_root, path):
                return False
            
            normalized_path = PathUtils.normalize_path(path)
            if normalized_path:
                full_path = self.manga_root / normalized_path
            else:
                full_path = self.manga_root
            
            return await aiofiles.os.path.isdir(full_path)
            
        except Exception as e:
            logger.debug(f"디렉토리 확인 실패: {path}, 오류: {e}")
            return False
    
    async def get_file_size(self, path: str) -> Optional[int]:
        """
        파일 크기 조회
        
        Args:
            path: 파일 경로
            
        Returns:
            Optional[int]: 파일 크기 (바이트), 실패 시 None
        """
        try:
            if not PathUtils.is_safe_path(self.manga_root, path):
                return None
            
            normalized_path = PathUtils.normalize_path(path)
            if normalized_path:
                full_path = self.manga_root / normalized_path
            else:
                full_path = self.manga_root
            
            if not await aiofiles.os.path.isfile(full_path):
                return None
            
            stat_result = await aiofiles.os.stat(full_path)
            return stat_result.st_size
            
        except Exception as e:
            logger.debug(f"파일 크기 조회 실패: {path}, 오류: {e}")
            return None
    
    def get_full_path(self, path: str) -> Optional[Path]:
        """
        상대 경로를 절대 경로로 변환
        
        Args:
            path: 상대 경로
            
        Returns:
            Optional[Path]: 절대 경로, 안전하지 않으면 None
        """
        try:
            if not PathUtils.is_safe_path(self.manga_root, path):
                return None
            
            normalized_path = PathUtils.normalize_path(path)
            if normalized_path:
                return self.manga_root / normalized_path
            else:
                return self.manga_root
                
        except Exception as e:
            logger.debug(f"절대 경로 변환 실패: {path}, 오류: {e}")
            return None