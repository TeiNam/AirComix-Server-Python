"""
간단한 테스트 케이스
GitHub Actions 디버깅용
"""

import os
import tempfile
from pathlib import Path


def test_basic_python():
    """기본 Python 기능 테스트"""
    assert 1 + 1 == 2
    assert "hello" == "hello"


def test_environment_variables():
    """환경 변수 테스트"""
    manga_dir = os.getenv("COMIX_MANGA_DIRECTORY")
    debug_mode = os.getenv("COMIX_DEBUG_MODE")
    
    print(f"MANGA_DIR: {manga_dir}")
    print(f"DEBUG_MODE: {debug_mode}")
    
    assert manga_dir is not None
    assert debug_mode == "true"


def test_temp_directory():
    """임시 디렉토리 생성 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        assert temp_path.exists()
        assert temp_path.is_dir()
        
        # 테스트 파일 생성
        test_file = temp_path / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()


def test_app_import():
    """앱 모듈 import 테스트"""
    try:
        import app
        print(f"App module path: {app.__file__}")
        assert True
    except ImportError as e:
        print(f"App import failed: {e}")
        assert False, f"Failed to import app module: {e}"


def test_config_import():
    """설정 모듈 import 테스트"""
    try:
        from app.models.config import Settings
        print("Settings class imported successfully")
        assert True
    except ImportError as e:
        print(f"Settings import failed: {e}")
        assert False, f"Failed to import Settings: {e}"


def test_settings_creation():
    """설정 인스턴스 생성 테스트"""
    try:
        from app.models.config import Settings
        
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            manga_dir = Path(temp_dir)
            
            # 설정 생성
            settings = Settings(
                manga_directory=manga_dir,
                debug_mode=True,
                enable_auth=False
            )
            
            assert settings.manga_directory == manga_dir
            assert settings.debug_mode is True
            assert settings.enable_auth is False
            print("Settings creation successful")
            
    except Exception as e:
        print(f"Settings creation failed: {e}")
        assert False, f"Failed to create settings: {e}"