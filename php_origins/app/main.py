"""Main application entry point for the comix server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.config import settings
from app.utils.logging import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting Comix Server Python Port")
    logger.info(f"Manga directory: {settings.manga_directory}")
    logger.info(f"Server will listen on {settings.server_host}:{settings.server_port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Comix Server Python Port")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Comix Server Python Port",
        description="A streaming server for comic books compatible with AirComix iOS app",
        version="1.0.0",
        lifespan=lifespan,
        debug=settings.debug_mode,
    )
    
    # Add CORS middleware if needed (for web clients)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug_mode else [],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    
    # TODO: Add API routes here in future tasks
    
    return app


# Create the application instance
app = create_app()


def main() -> None:
    """Main entry point for running the server."""
    import uvicorn
    
    # Setup logging before starting server
    setup_logging()
    
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower(),
        reload=settings.debug_mode,
    )


if __name__ == "__main__":
    main()