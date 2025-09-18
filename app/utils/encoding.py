"""
문자 인코딩 처리 유틸리티

아카이브 내 파일명의 인코딩 감지 및 변환을 담당
"""

import chardet
from typing import List, Optional

from app.models.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EncodingUtils:
    """문자 인코딩 처리 유틸리티 클래스"""
    
    @staticmethod
    def detect_and_convert_encoding(text: bytes) -> str:
        """
        바이트 문자열의 인코딩을 감지하고 UTF-8로 변환
        
        Args:
            text: 변환할 바이트 문자열
            
        Returns:
            str: UTF-8로 변환된 문자열
        """
        if not text:
            return ""
        
        # 이미 문자열인 경우 그대로 반환
        if isinstance(text, str):
            return text
        
        # chardet을 사용한 인코딩 감지
        try:
            detected = chardet.detect(text)
            if detected and detected['encoding']:
                confidence = detected.get('confidence', 0)
                encoding = detected['encoding']
                
                logger.debug(f"감지된 인코딩: {encoding} (신뢰도: {confidence:.2f})")
                
                # 신뢰도가 높은 경우 감지된 인코딩 사용
                if confidence > 0.7:
                    try:
                        return text.decode(encoding)
                    except (UnicodeDecodeError, LookupError) as e:
                        logger.debug(f"감지된 인코딩 {encoding} 디코딩 실패: {e}")
        except Exception as e:
            logger.debug(f"인코딩 감지 실패: {e}")
        
        # 폴백 인코딩들로 시도
        return EncodingUtils.safe_decode(text, settings.fallback_encodings)
    
    @staticmethod
    def safe_decode(text: bytes, fallback_encodings: List[str]) -> str:
        """
        여러 인코딩을 시도하여 안전하게 디코딩
        
        Args:
            text: 디코딩할 바이트 문자열
            fallback_encodings: 시도할 인코딩 목록
            
        Returns:
            str: 디코딩된 문자열
        """
        if not text:
            return ""
        
        if isinstance(text, str):
            return text
        
        # 설정된 소스 인코딩을 먼저 시도
        encodings_to_try = [settings.source_encoding] + fallback_encodings
        
        # 중복 제거하면서 순서 유지
        seen = set()
        unique_encodings = []
        for enc in encodings_to_try:
            if enc not in seen:
                seen.add(enc)
                unique_encodings.append(enc)
        
        for encoding in unique_encodings:
            try:
                decoded = text.decode(encoding)
                logger.debug(f"인코딩 {encoding}으로 디코딩 성공")
                return decoded
            except (UnicodeDecodeError, LookupError) as e:
                logger.debug(f"인코딩 {encoding} 디코딩 실패: {e}")
                continue
        
        # 모든 인코딩 실패 시 에러 무시하고 디코딩
        try:
            result = text.decode('utf-8', errors='ignore')
            logger.warning(f"모든 인코딩 실패, UTF-8 에러 무시로 디코딩: {result}")
            return result
        except Exception as e:
            logger.error(f"최종 디코딩 실패: {e}")
            return text.decode('latin1')  # latin1은 항상 성공
    
    @staticmethod
    def convert_filename_encoding(filename: str) -> str:
        """
        파일명 인코딩 변환 (PHP 버전과 호환성 유지)
        
        Args:
            filename: 변환할 파일명
            
        Returns:
            str: 변환된 파일명
        """
        if not filename:
            return ""
        
        # 이미 문자열인 경우
        if isinstance(filename, str):
            # UTF-8로 인코딩 후 다시 디코딩해서 유효성 검사
            try:
                filename.encode('utf-8')
                return filename
            except UnicodeEncodeError:
                # 인코딩 문제가 있는 경우 바이트로 변환 후 재처리
                filename_bytes = filename.encode('latin1')
                return EncodingUtils.detect_and_convert_encoding(filename_bytes)
        
        # 바이트인 경우
        return EncodingUtils.detect_and_convert_encoding(filename)
    
    @staticmethod
    def is_encoding_convertible(text: bytes, source_encoding: str) -> bool:
        """
        특정 인코딩으로 변환 가능한지 확인 (PHP 버전 호환성)
        
        Args:
            text: 확인할 바이트 문자열
            source_encoding: 소스 인코딩
            
        Returns:
            bool: 변환 가능 여부
        """
        if not text or isinstance(text, str):
            return True
        
        try:
            # 소스 인코딩으로 디코딩 후 다시 인코딩해서 길이 비교
            decoded = text.decode(source_encoding)
            re_encoded = decoded.encode(source_encoding)
            return len(re_encoded) == len(text)
        except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
            return False
    
    @staticmethod
    def normalize_encoding_name(encoding: str) -> str:
        """
        인코딩 이름 정규화
        
        Args:
            encoding: 정규화할 인코딩 이름
            
        Returns:
            str: 정규화된 인코딩 이름
        """
        if not encoding:
            return "utf-8"
        
        # 일반적인 인코딩 별칭 처리
        encoding_map = {
            'euc-kr': 'euc-kr',
            'euckr': 'euc-kr',
            'cp949': 'cp949',
            'ks_c_5601-1987': 'euc-kr',
            'utf8': 'utf-8',
            'utf-8': 'utf-8',
            'ascii': 'ascii',
            'latin1': 'latin-1',
            'latin-1': 'latin-1',
            'iso-8859-1': 'latin-1',
        }
        
        normalized = encoding.lower().replace('_', '-')
        return encoding_map.get(normalized, encoding)
    
    @staticmethod
    def get_mime_charset(encoding: str) -> str:
        """
        HTTP Content-Type에 사용할 charset 반환
        
        Args:
            encoding: 인코딩 이름
            
        Returns:
            str: MIME charset
        """
        charset_map = {
            'utf-8': 'utf-8',
            'euc-kr': 'euc-kr',
            'cp949': 'euc-kr',
            'ascii': 'ascii',
            'latin-1': 'iso-8859-1',
        }
        
        normalized = EncodingUtils.normalize_encoding_name(encoding)
        return charset_map.get(normalized, 'utf-8')