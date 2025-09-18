"""
경로 처리 유틸리티

경로 검증, 정규화, 보안 검사 등을 담당
"""

import os
import urllib.parse
from pathlib import Path
from typing import Tuple, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


class PathUtils:
    """경로 처리 유틸리티 클래스"""
    
    @staticmethod
    def is_safe_path(base_path: Path, requested_path: str) -> bool:
        """
        디렉토리 순회 공격 방지를 위한 경로 안전성 검사
        
        Args:
            base_path: 기준 경로 (manga 디렉토리)
            requested_path: 요청된 경로
            
        Returns:
            bool: 안전한 경로인지 여부
        """
        try:
            # base_path를 Path 객체로 변환 (이미 Path 객체인 경우에도 안전)
            base_path = Path(base_path)
            
            # URL 디코딩
            decoded_path = urllib.parse.unquote(requested_path)
            
            # 경로 정규화
            normalized_path = PathUtils.normalize_path(decoded_path)
            
            # 빈 경로는 안전함
            if not normalized_path:
                return True
            
            # 절대 경로인 경우 (/ 로 시작) 거부
            if decoded_path.startswith('/'):
                logger.warning(f"절대 경로 접근 시도 감지: {requested_path}")
                return False
            
            # 절대 경로로 변환
            full_path = (base_path / normalized_path).resolve()
            base_path_resolved = base_path.resolve()
            
            # 기준 경로 내부에 있는지 확인
            try:
                full_path.relative_to(base_path_resolved)
                return True
            except ValueError:
                logger.warning(f"경로 순회 공격 시도 감지: {requested_path}")
                return False
                
        except Exception as e:
            logger.error(f"경로 안전성 검사 중 오류: {e}")
            return False
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        경로 문자열 정규화
        
        Args:
            path: 정규화할 경로
            
        Returns:
            str: 정규화된 경로
        """
        if not path:
            return ""
        
        # 앞뒤 공백 제거
        path = path.strip()
        
        # 앞의 슬래시 제거 (상대 경로로 만들기)
        path = path.lstrip('/')
        
        # 백슬래시를 슬래시로 변환 (Windows 호환성)
        path = path.replace('\\', '/')
        
        # 연속된 슬래시 제거
        while '//' in path:
            path = path.replace('//', '/')
        
        # 뒤의 슬래시 제거 (디렉토리가 아닌 경우)
        path = path.rstrip('/')
        
        # 경로 정규화
        path = os.path.normpath(path)
        
        # Windows 스타일 경로를 Unix 스타일로 변환
        if os.sep != '/':
            path = path.replace(os.sep, '/')
        
        # '.'을 빈 문자열로 변환 (현재 디렉토리)
        if path == '.':
            path = ''
        
        return path
    
    @staticmethod
    def extract_archive_and_image_paths(full_path: str) -> Tuple[str, str]:
        """
        전체 경로에서 아카이브 경로와 내부 이미지 경로를 분리
        
        예: "manga/series/volume1.zip/page001.jpg" 
        -> ("manga/series/volume1.zip", "page001.jpg")
        
        Args:
            full_path: 전체 경로
            
        Returns:
            Tuple[str, str]: (아카이브 경로, 내부 이미지 경로)
        """
        # 지원하는 아카이브 확장자들
        archive_extensions = ['.zip', '.cbz', '.rar', '.cbr']
        
        full_path = PathUtils.normalize_path(full_path)
        
        for ext in archive_extensions:
            # 대소문자 구분 없이 검색
            lower_path = full_path.lower()
            ext_pos = lower_path.find(ext.lower())
            
            if ext_pos != -1:
                # 아카이브 파일 경로 추출 (실제 대소문자 유지)
                archive_end = ext_pos + len(ext)
                archive_path = full_path[:archive_end]
                
                # 내부 이미지 경로 추출
                remaining_path = full_path[archive_end:]
                image_path = remaining_path.lstrip('/')
                
                return archive_path, image_path
        
        # 아카이브가 아닌 경우 전체 경로를 파일 경로로 반환
        return full_path, ""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        파일명에서 확장자 추출
        
        Args:
            filename: 파일명
            
        Returns:
            str: 소문자 확장자 (점 제외)
        """
        if not filename:
            return ""
        
        ext = Path(filename).suffix.lower()
        return ext.lstrip('.')
    
    @staticmethod
    def is_archive_path(path: str) -> bool:
        """
        경로가 아카이브 내부 파일을 가리키는지 확인
        
        Args:
            path: 확인할 경로
            
        Returns:
            bool: 아카이브 내부 파일 경로인지 여부
        """
        archive_extensions = ['.zip', '.cbz', '.rar', '.cbr']
        lower_path = path.lower()
        
        for ext in archive_extensions:
            if ext in lower_path:
                # 확장자 뒤에 추가 경로가 있는지 확인
                ext_pos = lower_path.find(ext)
                remaining = path[ext_pos + len(ext):]
                return bool(remaining.strip('/'))
        
        return False
    
    @staticmethod
    def join_path(*parts: str) -> str:
        """
        경로 부분들을 안전하게 결합
        
        Args:
            *parts: 결합할 경로 부분들
            
        Returns:
            str: 결합된 경로
        """
        if not parts:
            return ""
        
        # 각 부분을 정규화하고 결합
        normalized_parts = []
        for part in parts:
            if part:
                normalized = PathUtils.normalize_path(str(part))
                if normalized:
                    normalized_parts.append(normalized)
        
        if not normalized_parts:
            return ""
        
        # 슬래시로 결합
        result = '/'.join(normalized_parts)
        
        # 최종 정규화
        return PathUtils.normalize_path(result)
    
    @staticmethod
    def get_parent_path(path: str) -> str:
        """
        경로의 부모 디렉토리 반환
        
        Args:
            path: 경로
            
        Returns:
            str: 부모 디렉토리 경로
        """
        normalized = PathUtils.normalize_path(path)
        if not normalized:
            return ""
        
        parent = str(Path(normalized).parent)
        if parent == '.':
            return ""
        
        return PathUtils.normalize_path(parent)
    
    @staticmethod
    def get_filename(path: str) -> str:
        """
        경로에서 파일명만 추출
        
        Args:
            path: 경로
            
        Returns:
            str: 파일명
        """
        normalized = PathUtils.normalize_path(path)
        if not normalized:
            return ""
        
        return Path(normalized).name