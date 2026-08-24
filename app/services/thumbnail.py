"""썸네일 생성 및 관리 서비스

아카이브 파일의 첫 번째 이미지를 썸네일로 생성하고 캐시합니다.
"""

import asyncio
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import io
from PIL import Image, ImageDraw, ImageFont

from app.models.config import settings
from app.services.archive import ArchiveService
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 썸네일 파일명은 md5 해시 32자 hex 이다. 맵핑 파일이 손상/조작된 경우
# 임의 경로가 삭제되지 않도록 이 형식만 신뢰한다.
THUMBNAIL_HASH_PATTERN = re.compile(r"^[0-9a-f]{32}$")

THUMBNAIL_SIZE = (200, 300)  # (폭, 높이)
JPEG_QUALITY = 85


def _is_valid_thumbnail_hash(value: str) -> bool:
    """썸네일 해시 형식(md5 hex 32자) 확인"""
    return bool(THUMBNAIL_HASH_PATTERN.match(value))


class ThumbnailService:
    """썸네일 생성 및 관리 서비스"""

    def __init__(self, archive_service: ArchiveService):
        self.archive_service = archive_service
        # 기본값은 manga 디렉토리 안의 숨김 폴더.
        # 읽기 전용 마운트 환경에서는 COMIX_THUMBNAIL_CACHE_DIRECTORY 로 옮길 수 있다.
        self.thumbnail_cache_dir = settings.thumbnail_cache_dir
        self.thumbnail_size = THUMBNAIL_SIZE
        self.mapping_file = self.thumbnail_cache_dir / "mapping.json"

        # 썸네일 캐시 디렉토리 생성
        self._ensure_cache_directory()

    # ------------------------------------------------------------------
    # 초기화
    # ------------------------------------------------------------------

    def _ensure_cache_directory(self) -> None:
        """썸네일 캐시 디렉토리 생성 및 초기 aircomix 썸네일 복사"""
        try:
            self.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"썸네일 캐시 디렉토리: {self.thumbnail_cache_dir}")

            # 처음 구동 시 aircomix 이미지를 캐시에 복사
            self._copy_initial_aircomix_thumbnail()

        except Exception as e:
            logger.error(f"썸네일 캐시 디렉토리 생성 실패: {e}")

    def _copy_initial_aircomix_thumbnail(self) -> None:
        """처음 구동 시 프로젝트 내 images/aircomix.jpg를 캐시 폴더에 복사"""
        try:
            manga_root = Path(settings.manga_directory)
            thumbnail_path = self._get_thumbnail_path(manga_root)

            # 이미 썸네일이 존재하면 복사하지 않음
            if thumbnail_path.exists():
                logger.debug("manga 루트 폴더 썸네일이 이미 존재함")
                return

            thumbnail_data = self._render_root_thumbnail()
            if thumbnail_data:
                thumbnail_path.write_bytes(thumbnail_data)
                logger.info(f"aircomix 썸네일 준비 완료: {thumbnail_path}")

        except Exception as e:
            logger.error(f"초기 aircomix 썸네일 준비 실패: {e}")

    # ------------------------------------------------------------------
    # 경로/맵핑
    # ------------------------------------------------------------------

    def _get_thumbnail_path(self, target_path: Path) -> Path:
        """대상 파일/폴더에 대한 썸네일 파일 경로 생성"""
        # 대상 경로의 해시를 사용하여 고유한 썸네일 파일명 생성
        target_hash = hashlib.md5(str(target_path).encode()).hexdigest()
        return self.thumbnail_cache_dir / f"{target_hash}.jpg"

    def _load_mapping_sync(self) -> Dict[str, Any]:
        """맵핑 파일 로드 (동기)"""
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"맵핑 파일 로드 실패: {e}")
            return {}

    def _save_mapping_sync(self, mapping: Dict[str, Any]) -> None:
        """맵핑 파일 저장 (동기, 원자적 교체)

        임시 파일에 쓰고 os.replace 로 바꿔치기한다. 여러 gunicorn 워커가
        동시에 저장해도 잘린 JSON 이 남지 않는다.
        """
        try:
            temp_file = self.mapping_file.with_suffix(f".tmp.{os.getpid()}")
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, self.mapping_file)
        except Exception as e:
            logger.error(f"맵핑 파일 저장 실패: {e}")

    async def _load_mapping(self) -> Dict[str, Any]:
        """썸네일 맵핑 파일 로드"""
        return await asyncio.to_thread(self._load_mapping_sync)

    async def _save_mapping(self, mapping: Dict[str, Any]) -> None:
        """썸네일 맵핑 파일 저장"""
        await asyncio.to_thread(self._save_mapping_sync, mapping)

    async def _update_mapping(self, thumbnail_hash: str, target_path: Path) -> None:
        """썸네일 맵핑 정보 업데이트

        ponytail: 프로세스 간 read-modify-write 경쟁은 마지막 저장이 이긴다.
        누락된 항목은 다음 썸네일 요청에서 다시 기록되고 cleanup 도 파일 존재를
        기준으로 동작하므로 실질적인 손해가 없다. 정밀한 동기화가 필요해지면
        맵핑을 별도 저장소로 옮긴다.
        """
        def _update() -> None:
            mapping = self._load_mapping_sync()
            mapping[thumbnail_hash] = {
                "original_path": str(target_path),
                "created_at": time.time(),
                "file_size": target_path.stat().st_size if target_path.exists() else 0
            }
            self._save_mapping_sync(mapping)

        await asyncio.to_thread(_update)

    # ------------------------------------------------------------------
    # 조회/생성
    # ------------------------------------------------------------------

    async def get_or_create_thumbnail(self, target_path: Path) -> Optional[bytes]:
        """썸네일을 가져오거나 생성합니다

        Args:
            target_path: 아카이브 파일 또는 폴더 경로

        Returns:
            썸네일 이미지 데이터 (JPEG), 실패 시 None
        """
        try:
            thumbnail_path = self._get_thumbnail_path(target_path)
            thumbnail_hash = thumbnail_path.stem

            # 기존 썸네일이 있고 최신인지 확인
            if await self._is_thumbnail_valid(thumbnail_path, target_path):
                logger.debug(f"기존 썸네일 사용: {thumbnail_path}")
                return await self._read_thumbnail(thumbnail_path)

            # 새 썸네일 생성
            logger.info(f"썸네일 생성 시작: {target_path.name}")

            is_file = await asyncio.to_thread(target_path.is_file)

            if is_file:
                # 아카이브 파일인 경우
                thumbnail_data = await self._create_thumbnail_from_archive(target_path)
            elif await asyncio.to_thread(target_path.is_dir):
                # 폴더인 경우 - 첫 번째 아카이브의 첫 번째 이미지 사용
                thumbnail_data = await self._create_thumbnail_from_directory(target_path)
            else:
                logger.warning(f"지원되지 않는 경로 타입: {target_path}")
                return None

            if thumbnail_data:
                # 썸네일을 캐시에 저장
                await self._save_thumbnail(thumbnail_path, thumbnail_data)
                # 맵핑 정보 업데이트
                await self._update_mapping(thumbnail_hash, target_path)
                logger.info(f"썸네일 생성 완료: {target_path.name}")
                return thumbnail_data

            return None

        except Exception as e:
            logger.error(f"썸네일 처리 실패: {target_path}, 오류: {e}")
            return None

    async def _is_thumbnail_valid(self, thumbnail_path: Path, target_path: Path) -> bool:
        """썸네일이 유효한지 확인 (존재하고 대상보다 최신인지)"""
        def _check() -> bool:
            if not thumbnail_path.exists():
                return False

            # 파일 수정 시간 비교
            return thumbnail_path.stat().st_mtime >= target_path.stat().st_mtime

        try:
            return await asyncio.to_thread(_check)
        except Exception as e:
            logger.debug(f"썸네일 유효성 확인 실패: {e}")
            return False

    async def _read_thumbnail(self, thumbnail_path: Path) -> Optional[bytes]:
        """썸네일 파일 읽기"""
        try:
            return await asyncio.to_thread(thumbnail_path.read_bytes)
        except Exception as e:
            logger.error(f"썸네일 읽기 실패: {thumbnail_path}, 오류: {e}")
            return None

    async def _save_thumbnail(self, thumbnail_path: Path, thumbnail_data: bytes) -> None:
        """썸네일을 캐시에 저장"""
        try:
            await asyncio.to_thread(thumbnail_path.write_bytes, thumbnail_data)
            logger.debug(f"썸네일 저장 완료: {thumbnail_path}")
        except Exception as e:
            logger.error(f"썸네일 저장 실패: {thumbnail_path}, 오류: {e}")

    async def _create_thumbnail_from_archive(self, archive_path: Path) -> Optional[bytes]:
        """아카이브의 첫 번째 이미지로 썸네일 생성"""
        try:
            # 아카이브 내 이미지 목록 조회
            image_list = await self.archive_service.list_archive_contents(archive_path)

            if not image_list:
                logger.warning(f"아카이브에 이미지가 없음: {archive_path}")
                return None

            # 첫 번째 이미지 추출
            first_image = image_list[0]
            logger.debug(f"첫 번째 이미지 사용: {first_image}")

            image_data = await self.archive_service.extract_file_from_archive(
                archive_path, first_image
            )

            if not image_data:
                logger.warning(f"이미지 추출 실패: {archive_path}:{first_image}")
                return None

            # PIL로 썸네일 생성
            return await self._resize_image(image_data)

        except Exception as e:
            logger.error(f"썸네일 생성 실패: {archive_path}, 오류: {e}")
            return None

    async def _create_thumbnail_from_directory(self, directory_path: Path) -> Optional[bytes]:
        """폴더 썸네일 생성

        manga 루트 폴더는 aircomix 이미지를, 작품 폴더는 첫 번째 아카이브(보통 1권)의
        첫 페이지를 사용한다.
        """
        try:
            manga_root = Path(settings.manga_directory)

            # manga 루트 폴더인 경우 aircomix 이미지 사용
            if directory_path == manga_root:
                return await self._create_root_folder_thumbnail(directory_path)

            # 작품 폴더인 경우 첫 번째 아카이브의 첫 번째 이미지 사용
            def _find_first_archive() -> Optional[Path]:
                archives = [
                    entry for entry in directory_path.iterdir()
                    if entry.is_file() and settings.is_archive_file(entry.name)
                ]
                if not archives:
                    return None
                # 파일명으로 정렬하여 첫 번째 아카이브 선택 (보통 1권)
                archives.sort(key=lambda x: x.name.lower())
                return archives[0]

            first_archive = await asyncio.to_thread(_find_first_archive)

            if first_archive is None:
                logger.warning(f"폴더에 아카이브 파일이 없음: {directory_path}")
                return None

            logger.debug(f"작품 폴더 썸네일용 첫 번째 아카이브: {first_archive.name}")

            # 첫 번째 아카이브에서 썸네일 생성
            return await self._create_thumbnail_from_archive(first_archive)

        except Exception as e:
            logger.error(f"폴더 썸네일 생성 실패: {directory_path}, 오류: {e}")
            return None

    async def _create_root_folder_thumbnail(self, manga_root: Path) -> Optional[bytes]:
        """manga 루트 폴더 썸네일 생성 - 캐시된 aircomix 썸네일 사용"""
        try:
            thumbnail_path = self._get_thumbnail_path(manga_root)
            root_hash = thumbnail_path.stem

            # 캐시된 썸네일이 있으면 사용
            cached = await self._read_thumbnail(thumbnail_path) if thumbnail_path.exists() else None

            if cached:
                logger.debug(f"캐시된 manga 루트 폴더 썸네일 사용: {thumbnail_path}")
                await self._update_mapping(root_hash, manga_root)
                return cached

            # 캐시가 없으면 새로 생성 (프로젝트 내 images/aircomix.jpg 또는 기본 이미지)
            thumbnail_data = await asyncio.to_thread(self._render_root_thumbnail)

            if thumbnail_data:
                await self._save_thumbnail(thumbnail_path, thumbnail_data)
                await self._update_mapping(root_hash, manga_root)
                logger.info(f"manga 루트 폴더 썸네일 생성: {thumbnail_path}")

            return thumbnail_data

        except Exception as e:
            logger.error(f"manga 루트 폴더 썸네일 생성 실패: {e}")
            return None

    # ------------------------------------------------------------------
    # 이미지 렌더링 (동기 - 스레드에서 호출)
    # ------------------------------------------------------------------

    def _render_root_thumbnail(self) -> Optional[bytes]:
        """루트 폴더용 썸네일 데이터 생성 (images/aircomix.jpg → 실패 시 기본 이미지)"""
        project_root = Path(__file__).parent.parent.parent
        aircomix_image = project_root / "images" / "aircomix.jpg"

        if aircomix_image.is_file():
            try:
                return self._resize_image_sync(aircomix_image.read_bytes())
            except Exception as e:
                logger.warning(f"images/aircomix.jpg 처리 실패, 기본 이미지 생성: {e}")

        return self._render_default_thumbnail()

    def _render_default_thumbnail(self) -> Optional[bytes]:
        """기본 AirComix 썸네일 생성 (images/aircomix.jpg가 없을 때)"""
        try:
            img = Image.new('RGB', THUMBNAIL_SIZE, color='#2C3E50')
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            text = "AirComix\nServer"
            width, height = THUMBNAIL_SIZE

            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                x = (width - (bbox[2] - bbox[0])) // 2
                y = (height - (bbox[3] - bbox[1])) // 2
                draw.text((x, y), text, fill='white', font=font, align='center')
            else:
                draw.text((50, 140), "AirComix", fill='white')
                draw.text((60, 160), "Server", fill='white')

            # 테두리 추가
            draw.rectangle([(5, 5), (width - 5, height - 5)], outline='#3498DB', width=3)

            output = io.BytesIO()
            img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.error(f"기본 aircomix 썸네일 생성 실패: {e}")
            return None

    def _resize_image_sync(self, image_data: bytes) -> Optional[bytes]:
        """이미지를 썸네일 크기로 리사이즈 (동기)"""
        with Image.open(io.BytesIO(image_data)) as img:
            # RGB로 변환 (JPEG 저장을 위해)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # 썸네일 생성 (비율 유지)
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            return output.getvalue()

    async def _resize_image(self, image_data: bytes) -> Optional[bytes]:
        """이미지를 썸네일 크기로 리사이즈 (PIL은 CPU 집약적이므로 스레드에서 실행)"""
        try:
            return await asyncio.to_thread(self._resize_image_sync, image_data)
        except Exception as e:
            logger.error(f"이미지 리사이즈 실패: {e}")
            return None

    # ------------------------------------------------------------------
    # 캐시 관리
    # ------------------------------------------------------------------

    async def cleanup_orphaned_thumbnails(self) -> int:
        """원본 파일이 없는 고아 썸네일들을 정리합니다

        Returns:
            삭제된 썸네일 개수
        """
        def _cleanup() -> int:
            mapping = self._load_mapping_sync()
            deleted_count = 0
            updated_mapping: Dict[str, Any] = {}

            for thumbnail_hash, info in mapping.items():
                # 맵핑 파일이 조작된 경우에도 캐시 디렉토리 밖을 건드리지 않는다
                if not _is_valid_thumbnail_hash(thumbnail_hash):
                    logger.warning(f"맵핑에 잘못된 썸네일 키가 있어 무시함: {thumbnail_hash!r}")
                    continue

                original_path = Path(info.get("original_path", ""))
                thumbnail_path = self.thumbnail_cache_dir / f"{thumbnail_hash}.jpg"

                # 원본 파일이 존재하면 맵핑 유지
                if original_path.exists():
                    updated_mapping[thumbnail_hash] = info
                    continue

                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                    deleted_count += 1
                    logger.info(f"고아 썸네일 삭제: {thumbnail_path} (원본: {original_path})")

            self._save_mapping_sync(updated_mapping)
            return deleted_count

        try:
            deleted_count = await asyncio.to_thread(_cleanup)

            if deleted_count > 0:
                logger.info(f"고아 썸네일 정리 완료: {deleted_count}개 삭제")

            return deleted_count

        except Exception as e:
            logger.error(f"썸네일 정리 실패: {e}")
            return 0

    async def clear_cache(self) -> None:
        """썸네일 캐시 전체 삭제"""
        def _clear() -> None:
            if not self.thumbnail_cache_dir.exists():
                return

            for thumbnail_file in self.thumbnail_cache_dir.glob("*.jpg"):
                thumbnail_file.unlink()

            if self.mapping_file.exists():
                self.mapping_file.unlink()

        try:
            await asyncio.to_thread(_clear)
            logger.info("썸네일 캐시 삭제 완료")
        except Exception as e:
            logger.error(f"썸네일 캐시 삭제 실패: {e}")

    async def get_cache_info(self) -> dict:
        """썸네일 캐시 정보 조회"""
        def _info() -> dict:
            if not self.thumbnail_cache_dir.exists():
                return {"count": 0, "size": 0}

            thumbnails = list(self.thumbnail_cache_dir.glob("*.jpg"))
            total_size = sum(f.stat().st_size for f in thumbnails)
            mapping = self._load_mapping_sync()

            return {
                "count": len(thumbnails),
                "size": total_size,
                "cache_dir": str(self.thumbnail_cache_dir),
                "mapping_count": len(mapping),
                "orphaned_check_available": True
            }

        try:
            return await asyncio.to_thread(_info)
        except Exception as e:
            logger.error(f"캐시 정보 조회 실패: {e}")
            return {"count": 0, "size": 0, "error": str(e)}
