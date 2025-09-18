"""
아카이브 처리 서비스

ZIP/CBZ, RAR/CBR 파일의 내용 조회 및 파일 추출을 담당
"""

import asyncio
import zipfile
from pathlib import Path
from typing import List, Optional, BinaryIO
import io

try:
    import rarfile
    RARFILE_AVAILABLE = True
except ImportError:
    RARFILE_AVAILABLE = False

from app.models.config import settings
from app.models.data import ArchiveEntry
from app.utils.logging import get_logger
from app.utils.encoding import EncodingUtils
from app.utils.path import PathUtils

logger = get_logger(__name__)


class ArchiveService:
    """아카이브 처리 서비스 클래스"""
    
    def __init__(self):
        """ArchiveService 초기화"""
        logger.debug("ArchiveService 초기화")
        if not RARFILE_AVAILABLE:
            logger.warning("rarfile 라이브러리가 설치되지 않음. RAR/CBR 파일 지원 불가")
    
    async def list_archive_contents(self, archive_path: Path) -> List[str]:
        """
        아카이브 내부 이미지 파일 목록 조회
        
        Args:
            archive_path: 아카이브 파일 경로
            
        Returns:
            List[str]: 이미지 파일명 목록
        """
        try:
            if not archive_path.exists():
                logger.warning(f"아카이브 파일이 존재하지 않음: {archive_path}")
                return []
            
            ext = PathUtils.get_file_extension(archive_path.name)
            
            if ext in ['zip', 'cbz']:
                return await self._list_zip_contents(archive_path)
            elif ext in ['rar', 'cbr']:
                return await self._list_rar_contents(archive_path)
            else:
                logger.warning(f"지원되지 않는 아카이브 형식: {ext}")
                return []
                
        except Exception as e:
            logger.error(f"아카이브 내용 조회 실패: {archive_path}, 오류: {e}")
            # ArchiveError는 다시 발생시켜서 핸들러에서 500 에러로 처리되도록 함
            from app.exceptions import ArchiveError
            if isinstance(e, ArchiveError):
                raise e
            # 다른 예외는 ArchiveError로 래핑
            raise ArchiveError(f"아카이브 처리 중 오류가 발생했습니다: {e}")
    
    async def _list_zip_contents(self, archive_path: Path) -> List[str]:
        """
        ZIP/CBZ 파일 내용 조회
        
        Args:
            archive_path: ZIP 파일 경로
            
        Returns:
            List[str]: 이미지 파일명 목록
        """
        try:
            # 비동기적으로 ZIP 파일 처리
            def _process_zip():
                image_files = []
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    for entry in zip_file.infolist():
                        # 디렉토리는 제외
                        if entry.is_dir():
                            continue
                        
                        # 파일명 인코딩 변환
                        filename = EncodingUtils.convert_filename_encoding(entry.filename)
                        
                        # 이미지 파일인지 확인
                        if settings.is_image_file(filename):
                            image_files.append(filename)
                
                return image_files
            
            # 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            image_files = await loop.run_in_executor(None, _process_zip)
            
            # 파일명 정렬
            image_files.sort()
            
            logger.debug(f"ZIP 파일 내 이미지 {len(image_files)}개 발견: {archive_path}")
            return image_files
            
        except zipfile.BadZipFile:
            logger.error(f"손상된 ZIP 파일: {archive_path}")
            from app.exceptions import ArchiveError
            raise ArchiveError(f"손상된 ZIP 파일: {archive_path}")
        except Exception as e:
            logger.error(f"ZIP 파일 처리 실패: {archive_path}, 오류: {e}")
            from app.exceptions import ArchiveError
            raise ArchiveError(f"ZIP 파일 처리 실패: {e}")
    
    async def _list_rar_contents(self, archive_path: Path) -> List[str]:
        """
        RAR/CBR 파일 내용 조회
        
        Args:
            archive_path: RAR 파일 경로
            
        Returns:
            List[str]: 이미지 파일명 목록
        """
        if not RARFILE_AVAILABLE:
            logger.error("rarfile 라이브러리가 설치되지 않음")
            return []
        
        try:
            # 비동기적으로 RAR 파일 처리
            def _process_rar():
                image_files = []
                with rarfile.RarFile(archive_path, 'r') as rar_file:
                    for entry in rar_file.infolist():
                        # 디렉토리는 제외
                        if entry.is_dir():
                            continue
                        
                        # 파일명 인코딩 변환
                        filename = EncodingUtils.convert_filename_encoding(entry.filename)
                        
                        # 이미지 파일인지 확인
                        if settings.is_image_file(filename):
                            image_files.append(filename)
                
                return image_files
            
            # 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            image_files = await loop.run_in_executor(None, _process_rar)
            
            # 파일명 정렬
            image_files.sort()
            
            logger.debug(f"RAR 파일 내 이미지 {len(image_files)}개 발견: {archive_path}")
            return image_files
            
        except rarfile.BadRarFile:
            logger.error(f"손상된 RAR 파일: {archive_path}")
            from app.exceptions import ArchiveError
            raise ArchiveError(f"손상된 RAR 파일: {archive_path}")
        except Exception as e:
            logger.error(f"RAR 파일 처리 실패: {archive_path}, 오류: {e}")
            from app.exceptions import ArchiveError
            raise ArchiveError(f"RAR 파일 처리 실패: {e}")
    
    async def extract_file_from_archive(self, archive_path: Path, file_path: str) -> Optional[bytes]:
        """
        아카이브에서 특정 파일 추출
        
        Args:
            archive_path: 아카이브 파일 경로
            file_path: 추출할 파일 경로 (아카이브 내부)
            
        Returns:
            Optional[bytes]: 파일 데이터, 실패 시 None
        """
        try:
            if not archive_path.exists():
                logger.warning(f"아카이브 파일이 존재하지 않음: {archive_path}")
                return None
            
            ext = PathUtils.get_file_extension(archive_path.name)
            
            if ext in ['zip', 'cbz']:
                return await self._extract_from_zip(archive_path, file_path)
            elif ext in ['rar', 'cbr']:
                return await self._extract_from_rar(archive_path, file_path)
            else:
                logger.warning(f"지원되지 않는 아카이브 형식: {ext}")
                return None
                
        except Exception as e:
            logger.error(f"파일 추출 실패: {archive_path}:{file_path}, 오류: {e}")
            return None
    
    async def _extract_from_zip(self, archive_path: Path, file_path: str) -> Optional[bytes]:
        """
        ZIP 파일에서 파일 추출
        
        Args:
            archive_path: ZIP 파일 경로
            file_path: 추출할 파일 경로
            
        Returns:
            Optional[bytes]: 파일 데이터
        """
        try:
            def _extract():
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    # 파일명 매칭 (인코딩 고려)
                    for entry in zip_file.infolist():
                        if entry.is_dir():
                            continue
                        
                        # 파일명 인코딩 변환
                        filename = EncodingUtils.convert_filename_encoding(entry.filename)
                        
                        # 파일명이 일치하는지 확인 (끝부분 매칭)
                        if filename.endswith(file_path) or filename == file_path:
                            logger.debug(f"ZIP에서 파일 추출: {filename}")
                            return zip_file.read(entry)
                
                return None
            
            # 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _extract)
            
            return data
            
        except zipfile.BadZipFile:
            logger.error(f"손상된 ZIP 파일: {archive_path}")
            return None
        except Exception as e:
            logger.error(f"ZIP 파일 추출 실패: {archive_path}:{file_path}, 오류: {e}")
            return None
    
    async def _extract_from_rar(self, archive_path: Path, file_path: str) -> Optional[bytes]:
        """
        RAR 파일에서 파일 추출
        
        Args:
            archive_path: RAR 파일 경로
            file_path: 추출할 파일 경로
            
        Returns:
            Optional[bytes]: 파일 데이터
        """
        if not RARFILE_AVAILABLE:
            logger.error("rarfile 라이브러리가 설치되지 않음")
            return None
        
        try:
            def _extract():
                with rarfile.RarFile(archive_path, 'r') as rar_file:
                    # 파일명 매칭 (인코딩 고려)
                    for entry in rar_file.infolist():
                        if entry.is_dir():
                            continue
                        
                        # 파일명 인코딩 변환
                        filename = EncodingUtils.convert_filename_encoding(entry.filename)
                        
                        # 파일명이 일치하는지 확인 (끝부분 매칭)
                        if filename.endswith(file_path) or filename == file_path:
                            logger.debug(f"RAR에서 파일 추출: {filename}")
                            return rar_file.read(entry)
                
                return None
            
            # 스레드 풀에서 실행
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, _extract)
            
            return data
            
        except rarfile.BadRarFile:
            logger.error(f"손상된 RAR 파일: {archive_path}")
            return None
        except Exception as e:
            logger.error(f"RAR 파일 추출 실패: {archive_path}:{file_path}, 오류: {e}")
            return None
    
    def is_archive_file(self, filename: str) -> bool:
        """
        파일이 지원되는 아카이브 형식인지 확인
        
        Args:
            filename: 확인할 파일명
            
        Returns:
            bool: 아카이브 파일 여부
        """
        return settings.is_archive_file(filename)
    
    async def get_archive_info(self, archive_path: Path) -> Optional[dict]:
        """
        아카이브 파일 정보 조회
        
        Args:
            archive_path: 아카이브 파일 경로
            
        Returns:
            Optional[dict]: 아카이브 정보 (파일 수, 총 크기 등)
        """
        try:
            if not archive_path.exists():
                return None
            
            ext = PathUtils.get_file_extension(archive_path.name)
            
            if ext in ['zip', 'cbz']:
                return await self._get_zip_info(archive_path)
            elif ext in ['rar', 'cbr']:
                return await self._get_rar_info(archive_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"아카이브 정보 조회 실패: {archive_path}, 오류: {e}")
            return None
    
    async def _get_zip_info(self, archive_path: Path) -> Optional[dict]:
        """ZIP 파일 정보 조회"""
        try:
            def _get_info():
                with zipfile.ZipFile(archive_path, 'r') as zip_file:
                    entries = []
                    total_size = 0
                    image_count = 0
                    
                    for entry in zip_file.infolist():
                        if entry.is_dir():
                            continue
                        
                        filename = EncodingUtils.convert_filename_encoding(entry.filename)
                        is_image = settings.is_image_file(filename)
                        
                        if is_image:
                            image_count += 1
                        
                        total_size += entry.file_size
                        
                        entries.append(ArchiveEntry(
                            name=filename,
                            size=entry.file_size,
                            is_image=is_image,
                            compressed_size=entry.compress_size
                        ))
                    
                    return {
                        'type': 'zip',
                        'total_files': len(entries),
                        'image_files': image_count,
                        'total_size': total_size,
                        'entries': entries
                    }
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _get_info)
            
        except Exception as e:
            logger.error(f"ZIP 정보 조회 실패: {archive_path}, 오류: {e}")
            return None
    
    async def _get_rar_info(self, archive_path: Path) -> Optional[dict]:
        """RAR 파일 정보 조회"""
        if not RARFILE_AVAILABLE:
            return None
        
        try:
            def _get_info():
                with rarfile.RarFile(archive_path, 'r') as rar_file:
                    entries = []
                    total_size = 0
                    image_count = 0
                    
                    for entry in rar_file.infolist():
                        if entry.is_dir():
                            continue
                        
                        filename = EncodingUtils.convert_filename_encoding(entry.filename)
                        is_image = settings.is_image_file(filename)
                        
                        if is_image:
                            image_count += 1
                        
                        total_size += entry.file_size
                        
                        entries.append(ArchiveEntry(
                            name=filename,
                            size=entry.file_size,
                            is_image=is_image,
                            compressed_size=entry.compress_size
                        ))
                    
                    return {
                        'type': 'rar',
                        'total_files': len(entries),
                        'image_files': image_count,
                        'total_size': total_size,
                        'entries': entries
                    }
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _get_info)
            
        except Exception as e:
            logger.error(f"RAR 정보 조회 실패: {archive_path}, 오류: {e}")
            return None