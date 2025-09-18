"""썸네일 생성 및 관리 서비스

아카이브 파일의 첫 번째 이미지를 썸네일로 생성하고 캐시합니다.
"""

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import io
import time

from app.models.config import settings
from app.services.archive import ArchiveService
from app.utils.logging import get_logger
from app.utils.path import PathUtils

logger = get_logger(__name__)


class ThumbnailService:
    """썸네일 생성 및 관리 서비스"""
    
    def __init__(self, archive_service: ArchiveService):
        self.archive_service = archive_service
        # 썸네일을 manga 디렉토리 안에 저장 (숨김 폴더로 처리됨)
        self.thumbnail_cache_dir = Path(settings.manga_directory) / ".thumbnails"
        self.thumbnail_size = (200, 300)  # 썸네일 크기 (폭, 높이)
        self.mapping_file = self.thumbnail_cache_dir / "mapping.json"
        
        # 썸네일 캐시 디렉토리 생성
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self) -> None:
        """썸네일 캐시 디렉토리 생성 및 초기 aircomix 썸네일 복사"""
        try:
            self.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"썸네일 캐시 디렉토리: {self.thumbnail_cache_dir}")
            
            # 처음 구동 시 aircomix.png를 .thumbnails에 복사
            self._copy_initial_aircomix_thumbnail()
            
        except Exception as e:
            logger.error(f"썸네일 캐시 디렉토리 생성 실패: {e}")
    
    def _copy_initial_aircomix_thumbnail(self) -> None:
        """처음 구동 시 프로젝트 내 images/aircomix.jpg를 .thumbnails 폴더에 복사"""
        try:
            manga_root = Path(settings.manga_directory)
            
            # manga 루트 폴더의 해시값으로 썸네일 파일명 생성
            root_hash = hashlib.md5(str(manga_root).encode()).hexdigest()
            thumbnail_path = self.thumbnail_cache_dir / f"{root_hash}.jpg"
            
            # 이미 썸네일이 존재하면 복사하지 않음
            if thumbnail_path.exists():
                logger.debug("manga 루트 폴더 썸네일이 이미 존재함")
                return
            
            # 프로젝트 내 images/aircomix.jpg 경로 (git 프로젝트 안에 있음)
            project_root = Path(__file__).parent.parent.parent  # app/services/thumbnail.py에서 프로젝트 루트로
            aircomix_image = project_root / "images" / "aircomix.jpg"
            
            if aircomix_image.exists() and aircomix_image.is_file():
                logger.info("처음 구동: images/aircomix.jpg를 썸네일 캐시에 복사")
                try:
                    # images/aircomix.jpg 읽기
                    with open(aircomix_image, 'rb') as f:
                        image_data = f.read()
                    
                    # PIL로 리사이즈
                    from PIL import Image
                    with Image.open(io.BytesIO(image_data)) as img:
                        # RGB로 변환 (JPEG 저장을 위해)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # 썸네일 생성 (비율 유지)
                        img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                        
                        # JPEG로 저장
                        img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
                    
                    logger.info(f"aircomix 썸네일 복사 완료: {thumbnail_path}")
                    
                except Exception as e:
                    logger.warning(f"images/aircomix.jpg 복사 실패, 기본 이미지 생성: {e}")
                    self._create_default_aircomix_file(thumbnail_path)
            else:
                # images/aircomix.jpg가 없으면 기본 이미지 생성
                logger.info("images/aircomix.jpg가 없어서 기본 썸네일 생성")
                self._create_default_aircomix_file(thumbnail_path)
                
        except Exception as e:
            logger.error(f"초기 aircomix 썸네일 복사 실패: {e}")
    
    def _create_default_aircomix_file(self, thumbnail_path: Path) -> None:
        """기본 AirComix 썸네일 파일 생성"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 기본 이미지 생성 (200x300 크기)
            img = Image.new('RGB', (200, 300), color='#2C3E50')
            draw = ImageDraw.Draw(img)
            
            # 텍스트 추가
            try:
                # 시스템 기본 폰트 사용
                font = ImageFont.load_default()
            except:
                font = None
            
            # AirComix 텍스트
            text = "AirComix\nServer"
            if font:
                # 텍스트 크기 계산
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 중앙 정렬
                x = (200 - text_width) // 2
                y = (300 - text_height) // 2
                
                draw.text((x, y), text, fill='white', font=font, align='center')
            else:
                # 폰트가 없으면 간단한 텍스트
                draw.text((50, 140), "AirComix", fill='white')
                draw.text((60, 160), "Server", fill='white')
            
            # 테두리 추가
            draw.rectangle([(5, 5), (195, 295)], outline='#3498DB', width=3)
            
            # 썸네일 크기로 조정
            img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # JPEG로 저장
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            logger.info(f"기본 aircomix 썸네일 생성 완료: {thumbnail_path}")
            
        except Exception as e:
            logger.error(f"기본 aircomix 썸네일 생성 실패: {e}")
    
    def _get_thumbnail_path(self, target_path: Path) -> Path:
        """대상 파일/폴더에 대한 썸네일 파일 경로 생성"""
        # 대상 경로의 해시를 사용하여 고유한 썸네일 파일명 생성
        target_hash = hashlib.md5(str(target_path).encode()).hexdigest()
        return self.thumbnail_cache_dir / f"{target_hash}.jpg"
    
    async def _load_mapping(self) -> Dict[str, Any]:
        """썸네일 맵핑 파일 로드"""
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"맵핑 파일 로드 실패: {e}")
            return {}
    
    async def _save_mapping(self, mapping: Dict[str, Any]) -> None:
        """썸네일 맵핑 파일 저장"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"맵핑 파일 저장 실패: {e}")
    
    async def _update_mapping(self, thumbnail_hash: str, target_path: Path) -> None:
        """썸네일 맵핑 정보 업데이트"""
        mapping = await self._load_mapping()
        mapping[thumbnail_hash] = {
            "original_path": str(target_path),
            "created_at": time.time(),
            "file_size": target_path.stat().st_size if target_path.exists() else 0
        }
        await self._save_mapping(mapping)
    
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
            
            if target_path.is_file():
                # 아카이브 파일인 경우
                thumbnail_data = await self._create_thumbnail_from_archive(target_path)
            elif target_path.is_dir():
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
        try:
            if not thumbnail_path.exists():
                return False
            
            # 파일 수정 시간 비교
            thumbnail_mtime = thumbnail_path.stat().st_mtime
            target_mtime = target_path.stat().st_mtime
            
            return thumbnail_mtime >= target_mtime
            
        except Exception as e:
            logger.debug(f"썸네일 유효성 확인 실패: {e}")
            return False
    
    async def _read_thumbnail(self, thumbnail_path: Path) -> Optional[bytes]:
        """썸네일 파일 읽기"""
        try:
            with open(thumbnail_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"썸네일 읽기 실패: {thumbnail_path}, 오류: {e}")
            return None
    
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
            thumbnail_data = await self._resize_image(image_data)
            return thumbnail_data
            
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {archive_path}, 오류: {e}")
            return None
    
    async def _create_thumbnail_from_directory(self, directory_path: Path) -> Optional[bytes]:
        """폴더 썸네일 생성 - manga 루트 폴더는 images/aircomix.jpg를 캐시에 복사, 작품 폴더는 1권의 1페이지"""
        try:
            manga_root = Path(settings.manga_directory)
            
            # manga 루트 폴더인 경우 images/aircomix.jpg를 캐시에 복사
            if directory_path == manga_root:
                return await self._create_root_folder_thumbnail(directory_path)
            
            # 작품 폴더인 경우 첫 번째 아카이브의 첫 번째 이미지 사용
            archive_files = []
            for file_path in directory_path.iterdir():
                if file_path.is_file() and settings.is_archive_file(file_path.name):
                    archive_files.append(file_path)
            
            if not archive_files:
                logger.warning(f"폴더에 아카이브 파일이 없음: {directory_path}")
                return None
            
            # 파일명으로 정렬하여 첫 번째 아카이브 선택 (보통 1권)
            archive_files.sort(key=lambda x: x.name.lower())
            first_archive = archive_files[0]
            
            logger.debug(f"작품 폴더 썸네일용 첫 번째 아카이브: {first_archive.name}")
            
            # 첫 번째 아카이브에서 썸네일 생성
            return await self._create_thumbnail_from_archive(first_archive)
            
        except Exception as e:
            logger.error(f"폴더 썸네일 생성 실패: {directory_path}, 오류: {e}")
            return None
    
    async def _create_root_folder_thumbnail(self, manga_root: Path) -> Optional[bytes]:
        """manga 루트 폴더 썸네일 생성 - 캐시된 aircomix 썸네일 사용"""
        try:
            # manga 루트 폴더의 해시값으로 썸네일 파일명 생성
            root_hash = hashlib.md5(str(manga_root).encode()).hexdigest()
            thumbnail_path = self.thumbnail_cache_dir / f"{root_hash}.jpg"
            
            # 캐시된 썸네일이 있으면 사용
            if thumbnail_path.exists():
                logger.debug(f"캐시된 manga 루트 폴더 썸네일 사용: {thumbnail_path}")
                with open(thumbnail_path, 'rb') as f:
                    thumbnail_data = f.read()
                # 맵핑 정보 업데이트
                await self._update_mapping(root_hash, manga_root)
                return thumbnail_data
            
            # 캐시가 없으면 새로 생성 (프로젝트 내 images/aircomix.jpg 또는 기본 이미지)
            project_root = Path(__file__).parent.parent.parent  # 프로젝트 루트
            aircomix_image = project_root / "images" / "aircomix.jpg"
            
            if aircomix_image.exists() and aircomix_image.is_file():
                logger.debug(f"images/aircomix.jpg로 썸네일 생성")
                try:
                    # images/aircomix.jpg 읽기
                    with open(aircomix_image, 'rb') as f:
                        image_data = f.read()
                    
                    # 리사이즈 후 캐시에 저장
                    thumbnail_data = await self._resize_image(image_data)
                    if thumbnail_data:
                        # 캐시에 저장
                        await self._save_thumbnail(thumbnail_path, thumbnail_data)
                        # 맵핑 정보 업데이트
                        await self._update_mapping(root_hash, manga_root)
                        logger.info(f"manga 루트 폴더 썸네일 생성: {thumbnail_path}")
                        return thumbnail_data
                    
                except Exception as e:
                    logger.warning(f"images/aircomix.jpg 처리 실패, 기본 이미지 생성: {e}")
            
            # images/aircomix.jpg가 없거나 처리 실패 시 기본 이미지 생성
            logger.info("기본 이미지로 썸네일 생성")
            thumbnail_data = await self._create_default_aircomix_thumbnail()
            if thumbnail_data:
                # 캐시에 저장
                await self._save_thumbnail(thumbnail_path, thumbnail_data)
                # 맵핑 정보 업데이트
                await self._update_mapping(root_hash, manga_root)
                logger.info(f"manga 루트 폴더 기본 썸네일 생성: {thumbnail_path}")
                return thumbnail_data
            
            return None
            
        except Exception as e:
            logger.error(f"manga 루트 폴더 썸네일 생성 실패: {e}")
            return None
    
    async def _create_default_aircomix_thumbnail(self) -> Optional[bytes]:
        """기본 AirComix 썸네일 생성 (images/aircomix.jpg가 없을 때)"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            def _create_default():
                # 기본 이미지 생성 (200x300 크기)
                img = Image.new('RGB', (200, 300), color='#2C3E50')
                draw = ImageDraw.Draw(img)
                
                # 텍스트 추가
                try:
                    # 시스템 기본 폰트 사용
                    font = ImageFont.load_default()
                except:
                    font = None
                
                # AirComix 텍스트
                text = "AirComix\nServer"
                if font:
                    # 텍스트 크기 계산
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    # 중앙 정렬
                    x = (200 - text_width) // 2
                    y = (300 - text_height) // 2
                    
                    draw.text((x, y), text, fill='white', font=font, align='center')
                else:
                    # 폰트가 없으면 간단한 텍스트
                    draw.text((50, 140), "AirComix", fill='white')
                    draw.text((60, 160), "Server", fill='white')
                
                # 테두리 추가
                draw.rectangle([(5, 5), (195, 295)], outline='#3498DB', width=3)
                
                # JPEG로 저장
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85, optimize=True)
                return output.getvalue()
            
            # 스레드 풀에서 실행 (PIL은 CPU 집약적)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _create_default)
            
        except Exception as e:
            logger.error(f"기본 aircomix 썸네일 생성 실패: {e}")
            return None
    
    async def _resize_image(self, image_data: bytes) -> Optional[bytes]:
        """이미지를 썸네일 크기로 리사이즈"""
        try:
            def _resize():
                # PIL로 이미지 열기
                with Image.open(io.BytesIO(image_data)) as img:
                    # RGB로 변환 (JPEG 저장을 위해)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # 썸네일 생성 (비율 유지)
                    img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                    
                    # JPEG로 저장
                    output = io.BytesIO()
                    img.save(output, format='JPEG', quality=85, optimize=True)
                    return output.getvalue()
            
            # 스레드 풀에서 실행 (PIL은 CPU 집약적)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _resize)
            
        except Exception as e:
            logger.error(f"이미지 리사이즈 실패: {e}")
            return None
    
    async def _save_thumbnail(self, thumbnail_path: Path, thumbnail_data: bytes) -> None:
        """썸네일을 캐시에 저장"""
        try:
            with open(thumbnail_path, 'wb') as f:
                f.write(thumbnail_data)
            logger.debug(f"썸네일 저장 완료: {thumbnail_path}")
            
        except Exception as e:
            logger.error(f"썸네일 저장 실패: {thumbnail_path}, 오류: {e}")
    
    async def cleanup_orphaned_thumbnails(self) -> int:
        """원본 파일이 없는 고아 썸네일들을 정리합니다
        
        Returns:
            삭제된 썸네일 개수
        """
        try:
            mapping = await self._load_mapping()
            deleted_count = 0
            updated_mapping = {}
            
            for thumbnail_hash, info in mapping.items():
                original_path = Path(info["original_path"])
                thumbnail_path = self.thumbnail_cache_dir / f"{thumbnail_hash}.jpg"
                
                # 원본 파일이 존재하는지 확인
                if original_path.exists():
                    # 원본이 존재하면 맵핑 유지
                    updated_mapping[thumbnail_hash] = info
                else:
                    # 원본이 없으면 썸네일 삭제
                    if thumbnail_path.exists():
                        thumbnail_path.unlink()
                        deleted_count += 1
                        logger.info(f"고아 썸네일 삭제: {thumbnail_path} (원본: {original_path})")
            
            # 업데이트된 맵핑 저장
            await self._save_mapping(updated_mapping)
            
            if deleted_count > 0:
                logger.info(f"고아 썸네일 정리 완료: {deleted_count}개 삭제")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"썸네일 정리 실패: {e}")
            return 0
    
    async def clear_cache(self) -> None:
        """썸네일 캐시 전체 삭제"""
        try:
            if self.thumbnail_cache_dir.exists():
                for thumbnail_file in self.thumbnail_cache_dir.glob("*.jpg"):
                    thumbnail_file.unlink()
                # 맵핑 파일도 삭제
                if self.mapping_file.exists():
                    self.mapping_file.unlink()
                logger.info("썸네일 캐시 삭제 완료")
        except Exception as e:
            logger.error(f"썸네일 캐시 삭제 실패: {e}")
    
    async def get_cache_info(self) -> dict:
        """썸네일 캐시 정보 조회"""
        try:
            if not self.thumbnail_cache_dir.exists():
                return {"count": 0, "size": 0}
            
            thumbnails = list(self.thumbnail_cache_dir.glob("*.jpg"))
            total_size = sum(f.stat().st_size for f in thumbnails)
            
            # 맵핑 정보도 포함
            mapping = await self._load_mapping()
            
            return {
                "count": len(thumbnails),
                "size": total_size,
                "cache_dir": str(self.thumbnail_cache_dir),
                "mapping_count": len(mapping),
                "orphaned_check_available": True
            }
            
        except Exception as e:
            logger.error(f"캐시 정보 조회 실패: {e}")
            return {"count": 0, "size": 0, "error": str(e)}