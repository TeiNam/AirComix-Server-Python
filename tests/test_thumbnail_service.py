"""ThumbnailService 테스트

캐시 경로 설정, 맵핑 파일 저장/정리 동작을 확인한다.
"""

import json
import zipfile
from pathlib import Path

import pytest
from PIL import Image
import io

from app.services.archive import ArchiveService
from app.services.thumbnail import ThumbnailService


def _make_archive(path: Path) -> None:
    """이미지 한 장이 든 ZIP 생성"""
    buffer = io.BytesIO()
    Image.new("RGB", (60, 90), "red").save(buffer, "JPEG")

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("page001.jpg", buffer.getvalue())


@pytest.fixture
def thumbnail_env(tmp_path, monkeypatch):
    """manga 디렉토리와 별도 캐시 디렉토리를 가진 환경"""
    from app.services import thumbnail as thumbnail_module

    manga_dir = tmp_path / "manga"
    manga_dir.mkdir()
    cache_dir = tmp_path / "cache"

    monkeypatch.setattr(thumbnail_module.settings, "manga_directory", manga_dir)
    monkeypatch.setattr(thumbnail_module.settings, "thumbnail_cache_directory", cache_dir)

    return manga_dir, cache_dir


def test_cache_directory_can_be_relocated(thumbnail_env):
    """캐시 디렉토리를 manga 디렉토리 밖으로 지정할 수 있다

    manga 디렉토리를 읽기 전용으로 마운트하는 배포에서 필요하다.
    """
    manga_dir, cache_dir = thumbnail_env

    service = ThumbnailService(ArchiveService())

    assert service.thumbnail_cache_dir == cache_dir
    assert cache_dir.is_dir()
    assert not (manga_dir / ".thumbnails").exists()


@pytest.mark.asyncio
async def test_get_or_create_thumbnail_caches_and_maps(thumbnail_env):
    """썸네일을 생성하면 캐시 파일과 맵핑 항목이 만들어진다"""
    manga_dir, cache_dir = thumbnail_env

    archive_path = manga_dir / "volume1.zip"
    _make_archive(archive_path)

    service = ThumbnailService(ArchiveService())

    data = await service.get_or_create_thumbnail(archive_path)

    assert data
    assert data[:2] == b"\xff\xd8"  # JPEG 헤더

    thumbnail_path = service._get_thumbnail_path(archive_path)
    assert thumbnail_path.exists()

    mapping = json.loads((cache_dir / "mapping.json").read_text(encoding="utf-8"))
    assert thumbnail_path.stem in mapping
    assert mapping[thumbnail_path.stem]["original_path"] == str(archive_path)

    # 두 번째 호출은 캐시를 사용한다 (같은 데이터)
    assert await service.get_or_create_thumbnail(archive_path) == data


@pytest.mark.asyncio
async def test_cleanup_removes_orphans_and_ignores_bad_keys(thumbnail_env):
    """고아 썸네일만 삭제하고, 조작된 맵핑 키는 무시한다"""
    manga_dir, cache_dir = thumbnail_env

    archive_path = manga_dir / "volume1.zip"
    _make_archive(archive_path)

    service = ThumbnailService(ArchiveService())
    await service.get_or_create_thumbnail(archive_path)

    live_hash = service._get_thumbnail_path(archive_path).stem

    # 원본이 사라진 항목 + 캐시 디렉토리 밖을 가리키는 조작된 키
    orphan_hash = "0" * 32
    (cache_dir / f"{orphan_hash}.jpg").write_bytes(b"orphan")

    outside_target = cache_dir.parent / "outside.jpg"
    outside_target.write_bytes(b"do not touch")

    mapping = json.loads((cache_dir / "mapping.json").read_text(encoding="utf-8"))
    mapping[orphan_hash] = {"original_path": str(manga_dir / "deleted.zip")}
    mapping["../outside"] = {"original_path": str(manga_dir / "deleted.zip")}
    (cache_dir / "mapping.json").write_text(json.dumps(mapping), encoding="utf-8")

    deleted = await service.cleanup_orphaned_thumbnails()

    assert deleted == 1
    assert not (cache_dir / f"{orphan_hash}.jpg").exists()
    # 조작된 키는 캐시 디렉토리 밖 파일을 건드리지 않는다
    assert outside_target.exists()

    remaining = json.loads((cache_dir / "mapping.json").read_text(encoding="utf-8"))
    assert list(remaining) == [live_hash]


@pytest.mark.asyncio
async def test_clear_cache_and_info(thumbnail_env):
    """캐시 정보 조회와 전체 삭제"""
    manga_dir, cache_dir = thumbnail_env

    archive_path = manga_dir / "volume1.zip"
    _make_archive(archive_path)

    service = ThumbnailService(ArchiveService())
    await service.get_or_create_thumbnail(archive_path)

    info = await service.get_cache_info()
    assert info["count"] >= 1
    assert info["cache_dir"] == str(cache_dir)

    await service.clear_cache()

    assert list(cache_dir.glob("*.jpg")) == []
    assert not (cache_dir / "mapping.json").exists()
