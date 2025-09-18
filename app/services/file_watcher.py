"""파일 시스템 감시 서비스

manga 디렉토리의 파일 변경을 실시간으로 감지하고 
썸네일 정리 및 캐시 무효화를 자동으로 처리합니다.
"""

import asyncio
from pathlib import Path
from typing import Optional, Set, Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.models.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class MangaFileSystemEventHandler(FileSystemEventHandler):
    """만화 파일 시스템 이벤트 핸들러"""
    
    def __init__(self, watcher_service: 'FileWatcherService'):
        super().__init__()
        self.watcher_service = watcher_service
        self.manga_root = Path(settings.manga_directory)
        
        # 감시할 파일 확장자들
        self.watched_extensions = set(
            settings.archive_extensions + settings.image_extensions
        )
        
        # 무시할 파일/폴더들
        self.ignored_names = set(settings.hidden_files + ['.thumbnails'])
        self.ignored_patterns = set(settings.hidden_patterns)
    
    def _should_process_event(self, event: FileSystemEvent) -> bool:
        """이벤트를 처리해야 하는지 확인"""
        try:
            path = Path(event.src_path)
            
            # 디렉토리 이벤트는 항상 처리
            if event.is_directory:
                # 숨김 폴더는 무시
                if path.name in self.ignored_names:
                    return False
                # 패턴 매칭 확인
                for pattern in self.ignored_patterns:
                    if pattern in path.name:
                        return False
                return True
            
            # 파일 이벤트는 확장자 확인
            if path.suffix.lower().lstrip('.') in self.watched_extensions:
                # 숨김 파일은 무시
                if path.name in self.ignored_names:
                    return False
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"이벤트 처리 확인 실패: {e}")
            return False
    
    def on_created(self, event: FileSystemEvent) -> None:
        """파일/폴더 생성 이벤트"""
        if self._should_process_event(event):
            logger.info(f"파일 생성 감지: {event.src_path}")
            self.watcher_service._schedule_async_task(
                self.watcher_service._handle_file_created(Path(event.src_path))
            )
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """파일/폴더 삭제 이벤트"""
        if self._should_process_event(event):
            logger.info(f"파일 삭제 감지: {event.src_path}")
            self.watcher_service._schedule_async_task(
                self.watcher_service._handle_file_deleted(Path(event.src_path))
            )
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """파일/폴더 이동 이벤트"""
        if hasattr(event, 'dest_path'):
            # 이동은 삭제 + 생성으로 처리
            if self._should_process_event(event):
                logger.info(f"파일 이동 감지: {event.src_path} -> {event.dest_path}")
                self.watcher_service._schedule_async_task(
                    self.watcher_service._handle_file_deleted(Path(event.src_path))
                )
                self.watcher_service._schedule_async_task(
                    self.watcher_service._handle_file_created(Path(event.dest_path))
                )
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """파일/폴더 수정 이벤트"""
        if not event.is_directory and self._should_process_event(event):
            logger.info(f"파일 수정 감지: {event.src_path}")
            self.watcher_service._schedule_async_task(
                self.watcher_service._handle_file_modified(Path(event.src_path))
            )


class FileWatcherService:
    """파일 시스템 감시 서비스"""
    
    def __init__(self, thumbnail_service: Optional[Any] = None):
        self.thumbnail_service = thumbnail_service
        self.manga_root = Path(settings.manga_directory)
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[MangaFileSystemEventHandler] = None
        self.is_running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # 이벤트 콜백들
        self.on_file_created_callbacks: Set[Callable] = set()
        self.on_file_deleted_callbacks: Set[Callable] = set()
        self.on_file_modified_callbacks: Set[Callable] = set()
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """이벤트 콜백 추가"""
        if event_type == "created":
            self.on_file_created_callbacks.add(callback)
        elif event_type == "deleted":
            self.on_file_deleted_callbacks.add(callback)
        elif event_type == "modified":
            self.on_file_modified_callbacks.add(callback)
    
    def remove_callback(self, event_type: str, callback: Callable) -> None:
        """이벤트 콜백 제거"""
        if event_type == "created":
            self.on_file_created_callbacks.discard(callback)
        elif event_type == "deleted":
            self.on_file_deleted_callbacks.discard(callback)
        elif event_type == "modified":
            self.on_file_modified_callbacks.discard(callback)
    
    def _schedule_async_task(self, coro) -> None:
        """스레드 안전한 방식으로 비동기 태스크 스케줄링"""
        try:
            if self.loop and not self.loop.is_closed():
                # 이벤트 루프가 있으면 스레드 안전하게 태스크 스케줄링
                asyncio.run_coroutine_threadsafe(coro, self.loop)
            else:
                logger.debug("이벤트 루프가 없어서 파일 이벤트 처리 건너뜀")
        except Exception as e:
            logger.error(f"비동기 태스크 스케줄링 실패: {e}")
    
    async def start_watching(self) -> None:
        """파일 시스템 감시 시작"""
        try:
            if self.is_running:
                logger.warning("파일 감시가 이미 실행 중입니다")
                return
            
            if not self.manga_root.exists():
                logger.error(f"감시할 디렉토리가 존재하지 않음: {self.manga_root}")
                return
            
            # 현재 이벤트 루프 저장
            self.loop = asyncio.get_running_loop()
            
            # 이벤트 핸들러 및 옵저버 생성
            self.event_handler = MangaFileSystemEventHandler(self)
            self.observer = Observer()
            
            # 재귀적으로 감시 시작
            self.observer.schedule(
                self.event_handler,
                str(self.manga_root),
                recursive=True
            )
            
            self.observer.start()
            self.is_running = True
            
            logger.info(f"파일 시스템 감시 시작: {self.manga_root}")
            
        except Exception as e:
            logger.error(f"파일 시스템 감시 시작 실패: {e}")
            self.is_running = False
    
    async def stop_watching(self) -> None:
        """파일 시스템 감시 중지"""
        try:
            if not self.is_running or not self.observer:
                return
            
            self.observer.stop()
            self.observer.join(timeout=5.0)  # 5초 대기
            
            self.observer = None
            self.event_handler = None
            self.loop = None
            self.is_running = False
            
            logger.info("파일 시스템 감시 중지")
            
        except Exception as e:
            logger.error(f"파일 시스템 감시 중지 실패: {e}")
    
    async def _handle_file_created(self, file_path: Path) -> None:
        """파일 생성 이벤트 처리"""
        try:
            logger.debug(f"파일 생성 처리: {file_path}")
            
            # 콜백 실행
            for callback in self.on_file_created_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(file_path)
                    else:
                        callback(file_path)
                except Exception as e:
                    logger.error(f"생성 콜백 실행 실패: {e}")
            
            # 새 아카이브 파일이면 썸네일 미리 생성
            if (file_path.is_file() and 
                self.thumbnail_service and 
                settings.is_archive_file(file_path.name)):
                
                logger.info(f"새 아카이브 파일 썸네일 생성: {file_path.name}")
                await self.thumbnail_service.get_or_create_thumbnail(file_path)
            
        except Exception as e:
            logger.error(f"파일 생성 이벤트 처리 실패: {file_path}, 오류: {e}")
    
    async def _handle_file_deleted(self, file_path: Path) -> None:
        """파일 삭제 이벤트 처리"""
        try:
            logger.debug(f"파일 삭제 처리: {file_path}")
            
            # 콜백 실행
            for callback in self.on_file_deleted_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(file_path)
                    else:
                        callback(file_path)
                except Exception as e:
                    logger.error(f"삭제 콜백 실행 실패: {e}")
            
            # 썸네일 정리 (비동기로 실행)
            if self.thumbnail_service:
                asyncio.create_task(self._cleanup_thumbnails_delayed())
            
        except Exception as e:
            logger.error(f"파일 삭제 이벤트 처리 실패: {file_path}, 오류: {e}")
    
    async def _handle_file_modified(self, file_path: Path) -> None:
        """파일 수정 이벤트 처리"""
        try:
            logger.debug(f"파일 수정 처리: {file_path}")
            
            # 콜백 실행
            for callback in self.on_file_modified_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(file_path)
                    else:
                        callback(file_path)
                except Exception as e:
                    logger.error(f"수정 콜백 실행 실패: {e}")
            
            # 아카이브 파일이 수정되면 썸네일 재생성
            if (file_path.is_file() and 
                self.thumbnail_service and 
                settings.is_archive_file(file_path.name)):
                
                # 기존 썸네일 삭제 후 재생성
                thumbnail_path = self.thumbnail_service._get_thumbnail_path(file_path)
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                    logger.info(f"수정된 아카이브 썸네일 재생성: {file_path.name}")
                    await self.thumbnail_service.get_or_create_thumbnail(file_path)
            
        except Exception as e:
            logger.error(f"파일 수정 이벤트 처리 실패: {file_path}, 오류: {e}")
    
    async def _cleanup_thumbnails_delayed(self) -> None:
        """지연된 썸네일 정리 (너무 자주 실행되지 않도록)"""
        try:
            # 5초 대기 후 정리 (여러 파일이 동시에 삭제될 수 있으므로)
            await asyncio.sleep(5)
            
            if self.thumbnail_service:
                deleted_count = await self.thumbnail_service.cleanup_orphaned_thumbnails()
                if deleted_count > 0:
                    logger.info(f"자동 썸네일 정리 완료: {deleted_count}개 삭제")
            
        except Exception as e:
            logger.error(f"자동 썸네일 정리 실패: {e}")
    
    def get_status(self) -> dict:
        """파일 감시 상태 조회"""
        return {
            "is_running": self.is_running,
            "manga_directory": str(self.manga_root),
            "watched_extensions": list(self.watched_extensions) if hasattr(self, 'watched_extensions') else [],
            "callback_counts": {
                "created": len(self.on_file_created_callbacks),
                "deleted": len(self.on_file_deleted_callbacks),
                "modified": len(self.on_file_modified_callbacks)
            }
        }