"""
인코딩 유틸리티 테스트
"""

import pytest

from app.utils.encoding import EncodingUtils


def test_safe_decode_utf8():
    """UTF-8 디코딩 테스트"""
    # 정상적인 UTF-8 문자열
    utf8_text = "안녕하세요".encode('utf-8')
    result = EncodingUtils.safe_decode(utf8_text, ['utf-8', 'euc-kr'])
    assert result == "안녕하세요"


def test_safe_decode_euc_kr():
    """EUC-KR 디코딩 테스트"""
    # EUC-KR로 인코딩된 문자열
    euc_kr_text = "안녕하세요".encode('euc-kr')
    result = EncodingUtils.safe_decode(euc_kr_text, ['euc-kr', 'utf-8'])
    assert result == "안녕하세요"


def test_safe_decode_fallback():
    """폴백 인코딩 테스트"""
    # CP949로 인코딩된 문자열을 EUC-KR 폴백으로 디코딩
    cp949_text = "안녕하세요".encode('cp949')
    result = EncodingUtils.safe_decode(cp949_text, ['utf-8', 'euc-kr', 'cp949'])
    assert result == "안녕하세요"


def test_safe_decode_string_input():
    """문자열 입력 처리 테스트"""
    # 이미 문자열인 경우
    result = EncodingUtils.safe_decode("안녕하세요", ['utf-8'])
    assert result == "안녕하세요"


def test_safe_decode_empty():
    """빈 입력 처리 테스트"""
    assert EncodingUtils.safe_decode(b"", ['utf-8']) == ""
    assert EncodingUtils.safe_decode("", ['utf-8']) == ""


def test_detect_and_convert_encoding():
    """인코딩 감지 및 변환 테스트"""
    # UTF-8 텍스트
    utf8_text = "Hello World 안녕하세요".encode('utf-8')
    result = EncodingUtils.detect_and_convert_encoding(utf8_text)
    assert result == "Hello World 안녕하세요"
    
    # EUC-KR 텍스트
    euc_kr_text = "안녕하세요".encode('euc-kr')
    result = EncodingUtils.detect_and_convert_encoding(euc_kr_text)
    assert result == "안녕하세요"


def test_convert_filename_encoding():
    """파일명 인코딩 변환 테스트"""
    # 정상적인 UTF-8 파일명
    result = EncodingUtils.convert_filename_encoding("한글파일.jpg")
    assert result == "한글파일.jpg"
    
    # 바이트 파일명
    filename_bytes = "한글파일.jpg".encode('euc-kr')
    result = EncodingUtils.convert_filename_encoding(filename_bytes)
    assert result == "한글파일.jpg"


def test_is_encoding_convertible():
    """인코딩 변환 가능성 테스트"""
    # EUC-KR로 인코딩 가능한 텍스트
    euc_kr_text = "안녕하세요".encode('euc-kr')
    assert EncodingUtils.is_encoding_convertible(euc_kr_text, 'euc-kr') is True
    
    # 문자열 입력
    assert EncodingUtils.is_encoding_convertible("안녕하세요", 'euc-kr') is True
    
    # 빈 입력
    assert EncodingUtils.is_encoding_convertible(b"", 'euc-kr') is True


def test_normalize_encoding_name():
    """인코딩 이름 정규화 테스트"""
    assert EncodingUtils.normalize_encoding_name("EUC-KR") == "euc-kr"
    assert EncodingUtils.normalize_encoding_name("euckr") == "euc-kr"
    assert EncodingUtils.normalize_encoding_name("UTF8") == "utf-8"
    assert EncodingUtils.normalize_encoding_name("utf-8") == "utf-8"
    assert EncodingUtils.normalize_encoding_name("CP949") == "cp949"
    assert EncodingUtils.normalize_encoding_name("") == "utf-8"


def test_get_mime_charset():
    """MIME charset 반환 테스트"""
    assert EncodingUtils.get_mime_charset("utf-8") == "utf-8"
    assert EncodingUtils.get_mime_charset("euc-kr") == "euc-kr"
    assert EncodingUtils.get_mime_charset("cp949") == "euc-kr"
    assert EncodingUtils.get_mime_charset("ascii") == "ascii"
    assert EncodingUtils.get_mime_charset("latin-1") == "iso-8859-1"
    assert EncodingUtils.get_mime_charset("unknown") == "utf-8"


def test_japanese_encoding():
    """일본어 인코딩 테스트"""
    # Shift-JIS로 인코딩된 일본어
    japanese_text = "こんにちは"
    try:
        shift_jis_bytes = japanese_text.encode('shift-jis')
        result = EncodingUtils.detect_and_convert_encoding(shift_jis_bytes)
        # 정확히 디코딩되거나 최소한 에러가 발생하지 않아야 함
        assert isinstance(result, str)
    except UnicodeEncodeError:
        # Shift-JIS로 인코딩할 수 없는 환경에서는 패스
        pass


def test_mixed_encoding():
    """혼합 인코딩 처리 테스트"""
    # ASCII + 한글이 섞인 텍스트
    mixed_text = "Volume1_한글제목.zip"
    utf8_bytes = mixed_text.encode('utf-8')
    result = EncodingUtils.detect_and_convert_encoding(utf8_bytes)
    assert result == mixed_text


def test_corrupted_encoding():
    """손상된 인코딩 처리 테스트"""
    # 무작위 바이트 시퀀스
    corrupted_bytes = b'\xff\xfe\x00\x01\x02\x03'
    result = EncodingUtils.safe_decode(corrupted_bytes, ['utf-8', 'euc-kr', 'latin1'])
    # 에러 없이 문자열이 반환되어야 함
    assert isinstance(result, str)


def test_php_compatibility():
    """PHP 버전과의 호환성 테스트"""
    # PHP에서 사용하던 EUC-KR 인코딩 변환 로직 테스트
    korean_filename = "한글_파일명.jpg"
    euc_kr_bytes = korean_filename.encode('euc-kr')
    
    # PHP의 change_encoding 함수와 유사한 동작 확인
    is_convertible = EncodingUtils.is_encoding_convertible(euc_kr_bytes, 'euc-kr')
    assert is_convertible is True
    
    converted = EncodingUtils.convert_filename_encoding(euc_kr_bytes)
    assert converted == korean_filename