#!/usr/bin/env python3
"""
Basic TomlEv Usage Example

This example shows how to use TomlEv for basic configuration management
with type-safe models and environment variable substitution.
"""

from tomlev import BaseConfigModel, TomlEv


class DatabaseConfig(BaseConfigModel):
    """Database configuration model."""

    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int


class RedisConfig(BaseConfigModel):
    """Redis configuration model."""

    host: str
    port: int
    db: int


class AppConfig(BaseConfigModel):
    """Application configuration model."""

    app_name: str
    debug: bool
    environment: str
    port: int
    log_level: str

    database: DatabaseConfig
    redis: RedisConfig


def main() -> None:
    """Load and display configuration."""
    # Load configuration
    config = TomlEv(AppConfig, "config.toml", ".env").validate()

    # Display configuration
    print("=" * 60)
    print("Application Configuration")
    print("=" * 60)
    print(f"App Name: {config.app_name}")
    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.debug}")
    print(f"Port: {config.port}")
    print(f"Log Level: {config.log_level}")

    print("\n" + "=" * 60)
    print("Database Configuration")
    print("=" * 60)
    print(f"Host: {config.database.host}")
    print(f"Port: {config.database.port}")
    print(f"Database: {config.database.name}")
    print(f"User: {config.database.user}")
    print(f"Password: {'*' * len(config.database.password)}")
    print(f"Pool Size: {config.database.pool_size}")

    print("\n" + "=" * 60)
    print("Redis Configuration")
    print("=" * 60)
    print(f"Host: {config.redis.host}")
    print(f"Port: {config.redis.port}")
    print(f"Database: {config.redis.db}")
    print("=" * 60)


if __name__ == "__main__":
    main()
