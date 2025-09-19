"""
데이터 모델 테스트
"""

import pytest
from pathlib import Path

from app.models.data import FileInfo, ArchiveEntry, ServerInfo


def test_file_info_creation():
    """FileInfo 생성 테스트"""
    file_info = FileInfo(
        name="test.jpg",
        path=Path("/test/test.jpg"),
        is_directory=False,
        is_archive=False,
        is_image=True,
        size=1024,
        mime_type="image/jpeg"
    )
    
    assert file_info.name == "test.jpg"
    assert file_info.is_image is True
    assert file_info.is_archive is False
    assert file_info.is_directory is False
    assert file_info.size == 1024


def test_file_info_directory():
    """디렉토리 FileInfo 테스트"""
    dir_info = FileInfo(
        name="manga",
        path=Path("/test/comix"),
        is_directory=True,
        is_archive=False,
        is_image=False
    )
    
    assert dir_info.is_directory is True
    assert dir_info.is_archive is False
    assert dir_info.is_image is False


def test_file_info_validation_error():
    """FileInfo 검증 에러 테스트"""
    # 디렉토리가 동시에 아카이브일 수 없음
    with pytest.raises(ValueError, match="디렉토리는 아카이브나 이미지가 될 수 없습니다"):
        FileInfo(
            name="test",
            path=Path("/test"),
            is_directory=True,
            is_archive=True,
            is_image=False
        )
    
    # 파일이 동시에 아카이브와 이미지일 수 없음
    with pytest.raises(ValueError, match="파일은 아카이브와 이미지를 동시에 가질 수 없습니다"):
        FileInfo(
            name="test.zip",
            path=Path("/test.zip"),
            is_directory=False,
            is_archive=True,
            is_image=True
        )


def test_archive_entry_creation():
    """ArchiveEntry 생성 테스트"""
    entry = ArchiveEntry(
        name="page001.jpg",
        size=2048,
        is_image=True,
        compressed_size=1024
    )
    
    assert entry.name == "page001.jpg"
    assert entry.size == 2048
    assert entry.is_image is True
    assert entry.compressed_size == 1024


def test_archive_entry_validation():
    """ArchiveEntry 검증 테스트"""
    # 음수 크기 불가
    with pytest.raises(ValueError, match="파일 크기는 0 이상이어야 합니다"):
        ArchiveEntry(
            name="test.jpg",
            size=-1,
            is_image=True
        )
    
    # 음수 압축 크기 불가
    with pytest.raises(ValueError, match="압축된 파일 크기는 0 이상이어야 합니다"):
        ArchiveEntry(
            name="test.jpg",
            size=1024,
            is_image=True,
            compressed_size=-1
        )


def test_server_info_creation():
    """ServerInfo 생성 테스트"""
    server_info = ServerInfo()
    
    assert server_info.message == "I am a generous god!"
    assert server_info.allow_download is True
    assert server_info.allow_image_process is True


def test_server_info_custom():
    """커스텀 ServerInfo 테스트"""
    server_info = ServerInfo(
        message="Custom message",
        allow_download=False,
        allow_image_process=False
    )
    
    assert server_info.message == "Custom message"
    assert server_info.allow_download is False
    assert server_info.allow_image_process is False


def test_server_info_response_string():
    """ServerInfo 응답 문자열 테스트"""
    server_info = ServerInfo()
    response = server_info.to_response_string()
    
    expected = (
        "I am a generous god!\r\n"
        "allowDownload=True\r\n"
        "allowImageProcess=True"
    )
    
    assert response == expected


def test_server_info_response_string_custom():
    """커스텀 ServerInfo 응답 문자열 테스트"""
    server_info = ServerInfo(
        message="Test server",
        allow_download=False,
        allow_image_process=True
    )
    response = server_info.to_response_string()
    
    expected = (
        "Test server\r\n"
        "allowDownload=False\r\n"
        "allowImageProcess=True"
    )
    
    assert response == expected