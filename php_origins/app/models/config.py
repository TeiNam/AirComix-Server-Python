"""Configuration models for the comix server."""

from pathlib import Path
from typing import List

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server configuration
    manga_directory: Path = Field(
        default=Path("/manga"),
        description="Root directory containing manga/comic collections"
    )
    server_port: int = Field(
        default=31257,
        ge=1,
        le=65535,
        description="Port for the server to listen on"
    )
    server_host: str = Field(
        default="0.0.0.0",
        description="Host address for the server to bind to"
    )
    
    # Application configuration
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode with detailed error messages"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # File filtering configuration
    hidden_files: List[str] = Field(
        default=[".", "..", "@eaDir", "Thumbs.db", ".DS_Store"],
        description="List of hidden files to filter out from listings"
    )
    hidden_patterns: List[str] = Field(
        default=["__MACOSX"],
        description="List of directory patterns to filter out"
    )
    
    # Supported file formats
    image_extensions: List[str] = Field(
        default=["jpg", "jpeg", "gif", "png", "tif", "tiff", "bmp"],
        description="Supported image file extensions"
    )
    archive_extensions: List[str] = Field(
        default=["zip", "cbz", "rar", "cbr"],
        description="Supported archive file extensions"
    )
    
    # Performance settings
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        description="Maximum file size to serve in bytes"
    )
    chunk_size: int = Field(
        default=8192,
        description="Chunk size for file streaming in bytes"
    )
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_prefix = "COMIX_"
        case_sensitive = False
        
    @validator("manga_directory")
    def validate_manga_directory(cls, v: Path) -> Path:
        """Validate that manga directory exists and is readable."""
        if not v.exists():
            raise ValueError(f"Manga directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Manga directory is not a directory: {v}")
        if not v.stat().st_mode & 0o444:  # Check read permission
            raise ValueError(f"Manga directory is not readable: {v}")
        return v.resolve()
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    @validator("image_extensions", "archive_extensions")
    def validate_extensions(cls, v: List[str]) -> List[str]:
        """Ensure extensions are lowercase and don't include dots."""
        return [ext.lower().lstrip('.') for ext in v]


# Global settings instance
settings = Settings()