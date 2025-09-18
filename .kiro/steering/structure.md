# Project Structure

## Directory Organization

```
app/                    # Main application package
├── __init__.py        # Package initialization
├── main.py            # Application entry point and FastAPI app creation
├── api/               # API route handlers (future)
│   └── __init__.py
├── models/            # Pydantic models and configuration
│   ├── __init__.py
│   └── config.py      # Settings and configuration models
├── services/          # Business logic and service layer (future)
│   └── __init__.py
└── utils/             # Utility functions and helpers
    ├── __init__.py
    └── logging.py     # Logging configuration and utilities

tests/                 # Test suite
├── __init__.py
├── conftest.py        # Pytest configuration and fixtures
└── test_*.py          # Test modules

conf/                  # Legacy PHP server configuration files
├── htaccess
└── httpd.conf-comix

.kiro/                 # Kiro IDE configuration
└── steering/          # AI assistant steering documents
```

## Code Organization Patterns

### Configuration Management
- All settings in `app/models/config.py` using Pydantic Settings
- Environment variables prefixed with `COMIX_`
- Settings validation with custom validators
- Global settings instance: `from app.models.config import settings`

### Logging
- Centralized logging setup in `app/utils/logging.py`
- Structured logging with consistent formatting
- Logger retrieval: `from app.utils.logging import get_logger`
- Performance and error logging utilities

### Application Structure
- FastAPI app creation in `app/main.py` with `create_app()` factory
- Lifespan management for startup/shutdown logic
- CORS middleware configuration based on debug mode
- Entry point script: `comix-server` command

### Testing
- Pytest with async support
- Test fixtures in `conftest.py` for common setup
- Temporary directories for file system testing
- Settings override pattern for test isolation

## File Naming Conventions
- Snake_case for Python files and directories
- Test files prefixed with `test_`
- Package initialization with `__init__.py` files
- Configuration files use descriptive names (`config.py`, `logging.py`)

## Import Patterns
- Absolute imports from `app` package root
- Type hints throughout the codebase
- Pydantic models for data validation
- Async/await for I/O operations