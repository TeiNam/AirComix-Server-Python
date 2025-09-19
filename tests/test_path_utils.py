"""
경로 유틸리티 테스트
"""

import tempfile
from pathlib import Path

import pytest

from app.utils.path import PathUtils


def test_normalize_path():
    """경로 정규화 테스트"""
    # 기본 정규화
    assert PathUtils.normalize_path("/comix/series/volume1") == "manga/series/volume1"
    assert PathUtils.normalize_path("manga//series///volume1") == "manga/series/volume1"
    assert PathUtils.normalize_path("manga\\series\\volume1") == "manga/series/volume1"
    
    # 공백 처리
    assert PathUtils.normalize_path("  /comix/series/  ") == "manga/series"
    assert PathUtils.normalize_path("") == ""
    
    # 특수 경우
    assert PathUtils.normalize_path("/") == ""
    assert PathUtils.normalize_path("./manga") == "manga"


def test_is_safe_path():
    """경로 안전성 검사 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir) / "manga"
        base_path.mkdir()
        
        # 안전한 경로들
        assert PathUtils.is_safe_path(base_path, "series/volume1") is True
        assert PathUtils.is_safe_path(base_path, "series/volume1.zip") is True
        assert PathUtils.is_safe_path(base_path, "") is True
        
        # 위험한 경로들 (디렉토리 순회 공격)
        assert PathUtils.is_safe_path(base_path, "../../../etc/passwd") is False
        assert PathUtils.is_safe_path(base_path, "series/../../etc/passwd") is False
        assert PathUtils.is_safe_path(base_path, "/etc/passwd") is False


def test_extract_archive_and_image_paths():
    """아카이브 및 이미지 경로 분리 테스트"""
    # ZIP 파일
    archive_path, image_path = PathUtils.extract_archive_and_image_paths(
        "manga/series/volume1.zip/page001.jpg"
    )
    assert archive_path == "manga/series/volume1.zip"
    assert image_path == "page001.jpg"
    
    # CBZ 파일
    archive_path, image_path = PathUtils.extract_archive_and_image_paths(
        "manga/series/volume1.cbz/subfolder/page001.jpg"
    )
    assert archive_path == "manga/series/volume1.cbz"
    assert image_path == "subfolder/page001.jpg"
    
    # RAR 파일
    archive_path, image_path = PathUtils.extract_archive_and_image_paths(
        "manga/series/volume1.rar/page001.jpg"
    )
    assert archive_path == "manga/series/volume1.rar"
    assert image_path == "page001.jpg"
    
    # 일반 파일 (아카이브 아님)
    archive_path, image_path = PathUtils.extract_archive_and_image_paths(
        "manga/series/page001.jpg"
    )
    assert archive_path == "manga/series/page001.jpg"
    assert image_path == ""
    
    # 대소문자 구분 없음
    archive_path, image_path = PathUtils.extract_archive_and_image_paths(
        "manga/series/Volume1.ZIP/Page001.JPG"
    )
    assert archive_path == "manga/series/Volume1.ZIP"
    assert image_path == "Page001.JPG"


def test_get_file_extension():
    """파일 확장자 추출 테스트"""
    assert PathUtils.get_file_extension("test.jpg") == "jpg"
    assert PathUtils.get_file_extension("test.JPG") == "jpg"
    assert PathUtils.get_file_extension("archive.zip") == "zip"
    assert PathUtils.get_file_extension("no_extension") == ""
    assert PathUtils.get_file_extension("") == ""
    assert PathUtils.get_file_extension("test.tar.gz") == "gz"


def test_is_archive_path():
    """아카이브 경로 확인 테스트"""
    # 아카이브 내부 파일
    assert PathUtils.is_archive_path("manga/volume1.zip/page001.jpg") is True
    assert PathUtils.is_archive_path("manga/volume1.cbz/page001.jpg") is True
    assert PathUtils.is_archive_path("manga/volume1.rar/page001.jpg") is True
    assert PathUtils.is_archive_path("manga/volume1.cbr/page001.jpg") is True
    
    # 아카이브 파일 자체
    assert PathUtils.is_archive_path("manga/volume1.zip") is False
    assert PathUtils.is_archive_path("manga/volume1.cbz") is False
    
    # 일반 파일
    assert PathUtils.is_archive_path("manga/page001.jpg") is False
    assert PathUtils.is_archive_path("manga/series/") is False


def test_join_path():
    """경로 결합 테스트"""
    assert PathUtils.join_path("manga", "series", "volume1") == "manga/series/volume1"
    assert PathUtils.join_path("/comix/", "/series/", "/volume1/") == "manga/series/volume1"
    assert PathUtils.join_path("manga", "", "volume1") == "manga/volume1"
    assert PathUtils.join_path("", "", "") == ""
    assert PathUtils.join_path("manga") == "manga"


def test_get_parent_path():
    """부모 경로 추출 테스트"""
    assert PathUtils.get_parent_path("manga/series/volume1") == "manga/series"
    assert PathUtils.get_parent_path("manga/series/volume1.zip") == "manga/series"
    assert PathUtils.get_parent_path("manga") == ""
    assert PathUtils.get_parent_path("") == ""
    assert PathUtils.get_parent_path("volume1.zip") == ""


def test_get_filename():
    """파일명 추출 테스트"""
    assert PathUtils.get_filename("manga/series/volume1.zip") == "volume1.zip"
    assert PathUtils.get_filename("manga/series/") == "series"
    assert PathUtils.get_filename("volume1.zip") == "volume1.zip"
    assert PathUtils.get_filename("") == ""
    assert PathUtils.get_filename("/comix/series/volume1") == "volume1"


def test_url_encoding():
    """URL 인코딩된 경로 처리 테스트"""
    # 한글 파일명이 URL 인코딩된 경우
    encoded_path = "manga/%ED%95%9C%EA%B8%80%20%EC%8B%9C%EB%A6%AC%EC%A6%88/volume1.zip"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir) / "manga"
        base_path.mkdir()
        
        # 한글 디렉토리 생성
        korean_dir = base_path / "한글 시리즈"
        korean_dir.mkdir()
        
        # URL 디코딩이 제대로 되는지 확인
        assert PathUtils.is_safe_path(base_path, encoded_path) is True


def test_edge_cases():
    """엣지 케이스 테스트"""
    # None 값 처리
    assert PathUtils.normalize_path(None) == ""
    assert PathUtils.get_file_extension(None) == ""
    
    # 매우 긴 경로
    long_path = "/".join(["very_long_directory_name"] * 100)
    normalized = PathUtils.normalize_path(long_path)
    assert len(normalized) > 0
    
    # 특수 문자가 포함된 경로
    special_path = "manga/series with spaces/volume[1].zip"
    normalized = PathUtils.normalize_path(special_path)
    assert "series with spaces" in normalized
    assert "volume[1].zip" in normalized