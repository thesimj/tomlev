#!/usr/bin/env python3
"""
FastAPI Integration with TomlEv

This example shows how to integrate TomlEv configuration management
with a FastAPI application using dependency injection.
"""

from functools import lru_cache

from tomlev import BaseConfigModel, TomlEv

# FastAPI imports are optional - this example works if you have them installed
try:
    import uvicorn
    from fastapi import Depends, FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")


# Configuration Models
class ServerConfig(BaseConfigModel):
    """Server configuration."""

    host: str
    port: int
    reload: bool


class APIConfig(BaseConfigModel):
    """API configuration."""

    prefix: str
    title: str
    description: str
    docs_url: str
    redoc_url: str


class CORSConfig(BaseConfigModel):
    """CORS configuration."""

    allow_origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]


class DatabaseConfig(BaseConfigModel):
    """Database configuration."""

    url: str
    pool_size: int
    max_overflow: int


class SecurityConfig(BaseConfigModel):
    """Security configuration."""

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


class AppConfig(BaseConfigModel):
    """Application configuration."""

    app_name: str
    version: str
    debug: bool

    server: ServerConfig
    api: APIConfig
    cors: CORSConfig
    database: DatabaseConfig
    security: SecurityConfig


# Configuration singleton
@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load configuration (cached)."""
    return TomlEv(AppConfig, "config.toml", ".env").validate()


if FASTAPI_AVAILABLE:
    # Create FastAPI app
    config = get_config()

    app = FastAPI(
        title=config.api.title,
        description=config.api.description,
        version=config.version,
        docs_url=config.api.docs_url,
        redoc_url=config.api.redoc_url,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=True,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "app": config.app_name,
            "version": config.version,
            "status": "running",
        }

    @app.get(f"{config.api.prefix}/config")
    async def get_app_config(cfg: AppConfig = Depends(get_config)) -> dict[str, str]:
        """Get non-sensitive configuration info."""
        return {
            "app_name": cfg.app_name,
            "version": cfg.version,
            "debug": str(cfg.debug),
            "api_prefix": cfg.api.prefix,
        }

    @app.get(f"{config.api.prefix}/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get(f"{config.api.prefix}/database")
    async def database_info(cfg: AppConfig = Depends(get_config)) -> dict[str, str]:
        """Get database configuration (without sensitive info)."""
        return {
            "pool_size": str(cfg.database.pool_size),
            "max_overflow": str(cfg.database.max_overflow),
            # Don't expose the actual URL with credentials
            "status": "configured",
        }

    def main() -> None:
        """Run the FastAPI application."""
        print("=" * 60)
        print("FastAPI + TomlEv Integration Example")
        print("=" * 60)
        print(f"App: {config.app_name}")
        print(f"Version: {config.version}")
        print(f"Debug: {config.debug}")
        print(f"Server: http://{config.server.host}:{config.server.port}")
        print(f"API Docs: http://{config.server.host}:{config.server.port}{config.api.docs_url}")
        print("=" * 60)

        uvicorn.run(
            "fastapi_app:app",
            host=config.server.host,
            port=config.server.port,
            reload=config.server.reload,
        )
else:

    def main() -> None:
        """Show config loading without FastAPI."""
        config = get_config()
        print("=" * 60)
        print("Configuration Loaded Successfully")
        print("=" * 60)
        print(f"App: {config.app_name}")
        print(f"Version: {config.version}")
        print(f"Debug: {config.debug}")
        print(f"Database Pool: {config.database.pool_size}")
        print("=" * 60)
        print("\nTo run the FastAPI server, install:")
        print("  pip install fastapi uvicorn")


if __name__ == "__main__":
    main()
