"""테스트용 설정 파일 생성 유틸리티"""

from pathlib import Path
from typing import Dict, Any
import json
import os


class TestConfigGenerator:
    """테스트용 설정 파일을 생성하는 클래스"""
    
    @staticmethod
    def create_test_env_file(env_path: Path, config: Dict[str, Any]) -> None:
        """테스트용 .env 파일을 생성합니다
        
        Args:
            env_path: .env 파일 경로
            config: 설정 딕셔너리
        """
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
    
    @staticmethod
    def get_minimal_config() -> Dict[str, Any]:
        """최소한의 테스트 설정을 반환합니다"""
        return {
            "COMIX_MANGA_DIRECTORY": "/tmp/test_manga",
            "COMIX_SERVER_PORT": "31257",
            "COMIX_DEBUG_MODE": "true"
        }
    
    @staticmethod
    def get_full_config() -> Dict[str, Any]:
        """전체 테스트 설정을 반환합니다"""
        return {
            "COMIX_MANGA_DIRECTORY": "/tmp/test_manga",
            "COMIX_SERVER_PORT": "31257",
            "COMIX_SERVER_HOST": "127.0.0.1",
            "COMIX_DEBUG_MODE": "true",
            "COMIX_LOG_LEVEL": "DEBUG",
            "COMIX_HIDDEN_FILES": ".DS_Store,Thumbs.db,@eaDir",
            "COMIX_HIDDEN_PATTERNS": "__MACOSX",
            "COMIX_IMAGE_EXTENSIONS": "jpg,jpeg,png,gif,bmp,tif,tiff",
            "COMIX_ARCHIVE_EXTENSIONS": "zip,cbz,rar,cbr",
            "COMIX_MAX_FILE_SIZE": "104857600",  # 100MB
            "COMIX_ENABLE_CORS": "true",
            "COMIX_CORS_ORIGINS": "http://localhost:3000,http://127.0.0.1:3000"
        }
    
    @staticmethod
    def get_production_config() -> Dict[str, Any]:
        """프로덕션 환경 테스트 설정을 반환합니다"""
        return {
            "COMIX_MANGA_DIRECTORY": "/manga",
            "COMIX_SERVER_PORT": "31257",
            "COMIX_SERVER_HOST": "0.0.0.0",
            "COMIX_DEBUG_MODE": "false",
            "COMIX_LOG_LEVEL": "INFO",
            "COMIX_ENABLE_CORS": "false"
        }
    
    @staticmethod
    def get_invalid_config() -> Dict[str, Any]:
        """유효하지 않은 설정을 반환합니다 (에러 테스트용)"""
        return {
            "COMIX_MANGA_DIRECTORY": "/nonexistent/directory",
            "COMIX_SERVER_PORT": "invalid_port",
            "COMIX_DEBUG_MODE": "invalid_boolean",
            "COMIX_LOG_LEVEL": "INVALID_LEVEL"
        }
    
    @staticmethod
    def create_all_test_configs(base_dir: Path) -> Dict[str, Path]:
        """모든 테스트 설정 파일을 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 설정 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # 최소 설정
        minimal_env = base_dir / ".env.minimal"
        TestConfigGenerator.create_test_env_file(minimal_env, TestConfigGenerator.get_minimal_config())
        paths["minimal"] = minimal_env
        
        # 전체 설정
        full_env = base_dir / ".env.full"
        TestConfigGenerator.create_test_env_file(full_env, TestConfigGenerator.get_full_config())
        paths["full"] = full_env
        
        # 프로덕션 설정
        prod_env = base_dir / ".env.production"
        TestConfigGenerator.create_test_env_file(prod_env, TestConfigGenerator.get_production_config())
        paths["production"] = prod_env
        
        # 유효하지 않은 설정
        invalid_env = base_dir / ".env.invalid"
        TestConfigGenerator.create_test_env_file(invalid_env, TestConfigGenerator.get_invalid_config())
        paths["invalid"] = invalid_env
        
        # 빈 설정 파일
        empty_env = base_dir / ".env.empty"
        empty_env.write_text("")
        paths["empty"] = empty_env
        
        return paths
    
    @staticmethod
    def create_docker_configs(base_dir: Path) -> Dict[str, Path]:
        """Docker 관련 설정 파일들을 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 Docker 설정 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # docker-compose.yml
        docker_compose_content = """version: '3.8'

services:
  comix-server:
    build: .
    ports:
      - "31257:31257"
    volumes:
      - ./test_manga:/manga:ro
    environment:
      - COMIX_MANGA_DIRECTORY=/manga
      - COMIX_DEBUG_MODE=false
      - COMIX_LOG_LEVEL=INFO
    restart: unless-stopped

  comix-server-dev:
    build: .
    ports:
      - "31258:31257"
    volumes:
      - ./test_manga:/manga:ro
      - .:/app
    environment:
      - COMIX_MANGA_DIRECTORY=/manga
      - COMIX_DEBUG_MODE=true
      - COMIX_LOG_LEVEL=DEBUG
    command: uvicorn app.main:app --host 0.0.0.0 --port 31257 --reload
"""
        
        docker_compose_path = base_dir / "docker-compose.test.yml"
        docker_compose_path.write_text(docker_compose_content)
        paths["docker_compose"] = docker_compose_path
        
        # Dockerfile.test
        dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \\
    unrar \\
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 테스트 실행
RUN python -m pytest tests/ -v

EXPOSE 31257

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "31257"]
"""
        
        dockerfile_path = base_dir / "Dockerfile.test"
        dockerfile_path.write_text(dockerfile_content)
        paths["dockerfile"] = dockerfile_path
        
        return paths