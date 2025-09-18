# Technology Stack

## Core Framework & Libraries
- **FastAPI**: Modern, high-performance web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation and settings management using Python type annotations
- **Pydantic Settings**: Environment variable configuration management

## File Processing
- **aiofiles**: Asynchronous file operations
- **Pillow**: Image processing and manipulation
- **rarfile**: RAR archive extraction support
- **python-multipart**: Multipart form data handling

## Development Tools
- **pytest**: Testing framework with async support
- **black**: Code formatting (line length: 88)
- **isort**: Import sorting (black profile)
- **mypy**: Static type checking
- **flake8**: Linting

## Build System
- **Hatchling**: Modern Python build backend
- **pyproject.toml**: Project configuration and dependencies

## Common Commands

### Development Setup
```bash
# Install in development mode
pip install -e ".[dev]"

# Install production dependencies only
pip install -e .
```

### Running the Server
```bash
# Using entry point
comix-server

# Using Python module
python -m app.main
```

### Code Quality
```bash
# Format code
black app tests
isort app tests

# Type checking
mypy app

# Linting
flake8 app tests
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_config.py
```

### Docker
```bash
# Build image
docker build -t comix-server .

# Run container
docker run -p 31257:31257 -v /path/to/manga:/manga comix-server
```

## Python Version
- Minimum: Python 3.11
- Target: Python 3.11-3.12