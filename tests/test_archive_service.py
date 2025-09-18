"""
아카이브 서비스 테스트
"""

import tempfile
import zipfile
from pathlib import Path
import pytest

from app.services.archive import ArchiveService
from app.exceptions import ArchiveError


@pytest.fixture
def sample_zip_file():
    """샘플 ZIP 파일 생성"""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "test.zip"
        
        # ZIP 파일 생성
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # 이미지 파일들 추가
            zip_file.writestr("page001.jpg", b"fake jpeg data")
            zip_file.writestr("page002.png", b"fake png data")
            zip_file.writestr("cover.gif", b"fake gif data")
            
            # 지원되지 않는 파일들
            zip_file.writestr("readme.txt", b"readme content")
            zip_file.writestr("info.xml", b"<info/>")
            
            # 디렉토리 구조
            zip_file.writestr("subfolder/page003.jpg", b"fake jpeg in subfolder")
        
        yield zip_path


@pytest.fixture
def corrupted_zip_file():
    """손상된 ZIP 파일 생성"""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "corrupted.zip"
        zip_path.write_bytes(b"This is not a valid zip file")
        yield zip_path


@pytest.mark.asyncio
async def test_archive_service_init():
    """ArchiveService 초기화 테스트"""
    service = ArchiveService()
    assert service is not None


@pytest.mark.asyncio
async def test_is_archive_file():
    """아카이브 파일 형식 확인 테스트"""
    service = ArchiveService()
    
    # 지원되는 아카이브 형식
    assert service.is_archive_file("test.zip") is True
    assert service.is_archive_file("test.cbz") is True
    assert service.is_archive_file("test.rar") is True
    assert service.is_archive_file("test.cbr") is True
    
    # 지원되지 않는 형식
    assert service.is_archive_file("test.jpg") is False
    assert service.is_archive_file("test.txt") is False


@pytest.mark.asyncio
async def test_list_zip_contents(sample_zip_file):
    """ZIP 파일 내용 목록 조회 테스트"""
    service = ArchiveService()
    
    contents = await service.list_archive_contents(sample_zip_file)
    
    # 이미지 파일들만 포함되어야 함
    expected_images = ["cover.gif", "page001.jpg", "page002.png", "subfolder/page003.jpg"]
    assert set(contents) == set(expected_images)
    
    # 지원되지 않는 파일들은 제외되어야 함
    assert "readme.txt" not in contents
    assert "info.xml" not in contents


@pytest.mark.asyncio
async def test_list_nonexistent_archive():
    """존재하지 않는 아카이브 파일 테스트"""
    service = ArchiveService()
    
    nonexistent_path = Path("/nonexistent/archive.zip")
    contents = await service.list_archive_contents(nonexistent_path)
    
    assert contents == []


@pytest.mark.asyncio
async def test_list_corrupted_zip(corrupted_zip_file):
    """손상된 ZIP 파일 테스트"""
    service = ArchiveService()
    
    # 손상된 ZIP 파일은 ArchiveError를 발생시켜야 함
    with pytest.raises(ArchiveError):
        await service.list_archive_contents(corrupted_zip_file)


@pytest.mark.asyncio
async def test_extract_file_from_zip(sample_zip_file):
    """ZIP 파일에서 파일 추출 테스트"""
    service = ArchiveService()
    
    # 존재하는 파일 추출
    data = await service.extract_file_from_archive(sample_zip_file, "page001.jpg")
    assert data is not None
    assert data == b"fake jpeg data"
    
    # 하위 폴더의 파일 추출
    data = await service.extract_file_from_archive(sample_zip_file, "subfolder/page003.jpg")
    assert data is not None
    assert data == b"fake jpeg in subfolder"
    
    # 존재하지 않는 파일
    data = await service.extract_file_from_archive(sample_zip_file, "nonexistent.jpg")
    assert data is None


@pytest.mark.asyncio
async def test_extract_from_nonexistent_archive():
    """존재하지 않는 아카이브에서 추출 테스트"""
    service = ArchiveService()
    
    nonexistent_path = Path("/nonexistent/archive.zip")
    data = await service.extract_file_from_archive(nonexistent_path, "test.jpg")
    
    assert data is None


@pytest.mark.asyncio
async def test_get_zip_info(sample_zip_file):
    """ZIP 파일 정보 조회 테스트"""
    service = ArchiveService()
    
    info = await service.get_archive_info(sample_zip_file)
    
    assert info is not None
    assert info['type'] == 'zip'
    assert info['total_files'] == 6  # 모든 파일 (이미지 + 텍스트)
    assert info['image_files'] == 4  # 이미지 파일만
    assert info['total_size'] > 0
    assert len(info['entries']) == 6


@pytest.mark.asyncio
async def test_unsupported_archive_format():
    """지원되지 않는 아카이브 형식 테스트"""
    service = ArchiveService()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 지원되지 않는 확장자
        unsupported_path = Path(temp_dir) / "test.7z"
        unsupported_path.write_bytes(b"fake 7z data")
        
        contents = await service.list_archive_contents(unsupported_path)
        assert contents == []
        
        data = await service.extract_file_from_archive(unsupported_path, "test.jpg")
        assert data is None
        
        info = await service.get_archive_info(unsupported_path)
        assert info is None


@pytest.mark.asyncio
async def test_empty_zip_file():
    """빈 ZIP 파일 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "empty.zip"
        
        # 빈 ZIP 파일 생성
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            pass  # 아무것도 추가하지 않음
        
        service = ArchiveService()
        
        contents = await service.list_archive_contents(zip_path)
        assert contents == []
        
        info = await service.get_archive_info(zip_path)
        assert info is not None
        assert info['total_files'] == 0
        assert info['image_files'] == 0


@pytest.mark.asyncio
async def test_zip_with_korean_filenames():
    """한글 파일명이 포함된 ZIP 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "korean.zip"
        
        # 한글 파일명으로 ZIP 파일 생성
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            # UTF-8로 인코딩된 한글 파일명
            zip_file.writestr("한글파일.jpg", b"korean image data")
            zip_file.writestr("폴더/이미지.png", b"korean image in folder")
        
        service = ArchiveService()
        
        contents = await service.list_archive_contents(zip_path)
        
        # 한글 파일명이 제대로 처리되어야 함
        assert len(contents) == 2
        assert any("한글파일.jpg" in name for name in contents)
        assert any("이미지.png" in name for name in contents)


def test_archive_service_without_rarfile():
    """rarfile 없이 ArchiveService 테스트"""
    # rarfile이 없는 상황을 시뮬레이션하기 위해
    # 실제로는 설치되어 있을 수 있지만 테스트 목적으로 확인
    service = ArchiveService()
    
    # RAR 파일 형식은 여전히 인식해야 함
    assert service.is_archive_file("test.rar") is True
    assert service.is_archive_file("test.cbr") is True