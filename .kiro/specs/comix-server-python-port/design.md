# Design Document

## Overview

This document describes the design for porting the PHP-based comix-server to Python. The new implementation will use FastAPI as the web framework to provide a modern, high-performance, and maintainable solution while maintaining full compatibility with the existing AirComix iOS app protocol.

The design focuses on clean architecture principles, proper separation of concerns, and efficient handling of file operations and archive processing. The server will be containerizable and easily deployable in modern environments.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AirComix      │    │   FastAPI       │    │   File System  │
│   iOS App       │◄──►│   Web Server    │◄──►│   & Archives    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Business      │
                       │   Logic Layer   │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Data Access   │
                       │   Layer         │
                       └─────────────────┘
```

### Technology Stack

- **Web Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn for development, Gunicorn + Uvicorn workers for production
- **Archive Processing**: 
  - `zipfile` (built-in) for ZIP/CBZ files
  - `rarfile` for RAR/CBR files
- **Configuration**: Pydantic Settings for type-safe configuration
- **Logging**: Python's built-in logging with structured output
- **Image Processing**: Pillow for MIME type detection and basic image operations
- **File Operations**: `aiofiles` for async file I/O

## Components and Interfaces

### 1. Web Layer (`app/api/`)

#### Router Structure
```python
# app/api/routes.py
@app.get("/")
async def get_root_directory_name()

@app.get("/welcome.102")
async def get_server_info()

@app.get("/manga/{path:path}")
async def handle_manga_request(path: str)
```

#### Request Handler
```python
class MangaRequestHandler:
    async def handle_request(self, path: str) -> Response:
        """Main request dispatcher based on path type"""
        
    async def handle_directory_listing(self, path: Path) -> PlainTextResponse:
        """Handle directory listing requests"""
        
    async def handle_archive_listing(self, archive_path: Path) -> PlainTextResponse:
        """Handle archive file listing requests"""
        
    async def handle_image_request(self, image_path: Path) -> StreamingResponse:
        """Handle individual image requests"""
```

### 2. Business Logic Layer (`app/services/`)

#### File System Service
```python
class FileSystemService:
    def __init__(self, manga_root: Path, config: Settings):
        self.manga_root = manga_root
        self.config = config
    
    async def list_directory(self, path: Path) -> List[str]:
        """List files and directories, applying filters"""
        
    async def is_supported_file(self, filename: str) -> bool:
        """Check if file is supported (image or archive)"""
        
    async def get_file_info(self, path: Path) -> FileInfo:
        """Get file metadata and type information"""
```

#### Archive Service
```python
class ArchiveService:
    async def list_archive_contents(self, archive_path: Path) -> List[str]:
        """List image files within an archive"""
        
    async def extract_file_from_archive(self, archive_path: Path, file_path: str) -> bytes:
        """Extract a specific file from an archive"""
        
    def is_archive_file(self, filename: str) -> bool:
        """Check if file is a supported archive format"""
```

#### Image Service
```python
class ImageService:
    async def stream_image(self, image_path: Path) -> StreamingResponse:
        """Stream image file with appropriate headers"""
        
    async def stream_image_from_archive(self, archive_path: Path, image_path: str) -> StreamingResponse:
        """Stream image from within an archive"""
        
    def get_mime_type(self, filename: str) -> str:
        """Determine MIME type from file extension"""
```

### 3. Data Models (`app/models/`)

#### Configuration Model
```python
class Settings(BaseSettings):
    manga_directory: Path = Path("/manga")
    server_port: int = 31257
    server_host: str = "0.0.0.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # File filtering
    hidden_files: List[str] = [".", "..", "@eaDir", "Thumbs.db", ".DS_Store"]
    hidden_patterns: List[str] = ["__MACOSX"]
    
    # Supported formats
    image_extensions: List[str] = ["jpg", "jpeg", "gif", "png", "tif", "tiff", "bmp"]
    archive_extensions: List[str] = ["zip", "cbz", "rar", "cbr"]
    
    class Config:
        env_file = ".env"
        env_prefix = "COMIX_"
```

#### Data Transfer Objects
```python
@dataclass
class FileInfo:
    name: str
    path: Path
    is_directory: bool
    is_archive: bool
    is_image: bool
    size: Optional[int] = None
    mime_type: Optional[str] = None

@dataclass
class ArchiveEntry:
    name: str
    size: int
    is_image: bool
```

### 4. Utilities (`app/utils/`)

#### Path Utilities
```python
class PathUtils:
    @staticmethod
    def is_safe_path(base_path: Path, requested_path: str) -> bool:
        """Prevent directory traversal attacks"""
        
    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize and clean path strings"""
        
    @staticmethod
    def extract_archive_and_image_paths(full_path: str) -> Tuple[str, str]:
        """Split path into archive path and internal image path"""
```

#### Encoding Utilities
```python
class EncodingUtils:
    @staticmethod
    def detect_and_convert_encoding(text: bytes) -> str:
        """Detect and convert text encoding for archive entries"""
        
    @staticmethod
    def safe_decode(text: bytes, fallback_encodings: List[str]) -> str:
        """Safely decode text with fallback options"""
```

## Data Models

### File System Structure
```
manga_root/
├── Series A/
│   ├── Volume 1.zip
│   ├── Volume 2.cbz
│   └── cover.jpg
├── Series B/
│   └── Chapter 001/
│       ├── page001.jpg
│       ├── page002.jpg
│       └── ...
└── ...
```

### Request/Response Flow

#### Directory Listing Request
```
GET /manga/Series%20A/
↓
1. Decode URL path
2. Validate path safety
3. Check if directory exists
4. List directory contents
5. Filter supported files
6. Return newline-separated list
```

#### Archive Listing Request
```
GET /manga/Series%20A/Volume%201.zip
↓
1. Decode URL path
2. Validate path safety
3. Check if archive exists
4. Open archive
5. List image files inside
6. Return newline-separated list
```

#### Image Request
```
GET /manga/Series%20A/Volume%201.zip/page001.jpg
↓
1. Parse path to extract archive and image paths
2. Validate paths
3. Open archive
4. Extract image file
5. Stream with appropriate headers
```

## Error Handling

### Error Response Strategy
```python
class ComixServerException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

class FileNotFoundError(ComixServerException):
    def __init__(self, path: str):
        super().__init__(f"File not found: {path}", 404)

class AccessDeniedError(ComixServerException):
    def __init__(self, path: str):
        super().__init__(f"Access denied: {path}", 403)

class ArchiveError(ComixServerException):
    def __init__(self, message: str):
        super().__init__(f"Archive error: {message}", 500)
```

### Global Exception Handler
```python
@app.exception_handler(ComixServerException)
async def comix_exception_handler(request: Request, exc: ComixServerException):
    return PlainTextResponse(
        content=exc.message if settings.debug_mode else "Internal Server Error",
        status_code=exc.status_code
    )
```

## Testing Strategy

### Unit Tests
- **Service Layer Tests**: Test business logic in isolation
- **Utility Tests**: Test path validation, encoding conversion
- **Model Tests**: Test configuration validation

### Integration Tests
- **API Endpoint Tests**: Test complete request/response cycles
- **File System Tests**: Test with real file structures
- **Archive Tests**: Test with sample ZIP/RAR files

### Test Structure
```
tests/
├── unit/
│   ├── test_file_system_service.py
│   ├── test_archive_service.py
│   ├── test_image_service.py
│   └── test_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_archive_handling.py
│   └── test_file_streaming.py
├── fixtures/
│   ├── sample_manga/
│   ├── test_archives/
│   └── test_images/
└── conftest.py
```

### Test Data Setup
```python
@pytest.fixture
def sample_manga_structure(tmp_path):
    """Create a sample manga directory structure for testing"""
    manga_dir = tmp_path / "manga"
    manga_dir.mkdir()
    
    # Create test directories and files
    series_a = manga_dir / "Series A"
    series_a.mkdir()
    
    # Create test ZIP file with images
    # Create test image files
    # Return manga_dir path
```

## Deployment Considerations

### Docker Configuration
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 31257

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "31257"]
```

### Environment Configuration
```yaml
# docker-compose.yml
version: '3.8'
services:
  comix-server:
    build: .
    ports:
      - "31257:31257"
    volumes:
      - /path/to/manga:/manga:ro
    environment:
      - COMIX_MANGA_DIRECTORY=/manga
      - COMIX_DEBUG_MODE=false
      - COMIX_LOG_LEVEL=INFO
```

### Production Deployment
- Use Gunicorn with Uvicorn workers for production
- Configure proper logging and monitoring
- Set up health check endpoints
- Configure reverse proxy (nginx) if needed
- Implement proper security headers and CORS if required