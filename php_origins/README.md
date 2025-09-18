# Comix Server Python Port

A Python port of the PHP-based comix-server for streaming comic books to the AirComix iOS app.

## Features

- FastAPI-based web server for high performance
- Support for ZIP/CBZ and RAR/CBR archive formats
- Direct image file serving
- Compatible with AirComix iOS app protocol
- Configurable via environment variables
- Docker support for easy deployment

## Quick Start

1. Install dependencies:
```bash
pip install -e .
```

2. Configure the server:
```bash
cp .env.example .env
# Edit .env with your manga directory path
```

3. Run the server:
```bash
comix-server
```

Or using Python directly:
```bash
python -m app.main
```

## Configuration

The server can be configured using environment variables or a `.env` file. See `.env.example` for all available options.

Key settings:
- `COMIX_MANGA_DIRECTORY`: Path to your manga/comic collection
- `COMIX_SERVER_PORT`: Port to listen on (default: 31257)
- `COMIX_DEBUG_MODE`: Enable debug mode (default: false)

## Development

Install development dependencies:
```bash
pip install -e ".[dev]"
```

Run tests:
```bash
pytest
```

Format code:
```bash
black app tests
isort app tests
```

## Docker

Build and run with Docker:
```bash
docker build -t comix-server .
docker run -p 31257:31257 -v /path/to/manga:/manga comix-server
```

## License

MIT License