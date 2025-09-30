#!/usr/bin/env python3
"""
Advanced TomlEv Usage Example

Demonstrates:
- Config file includes using __include
- Complex types (lists, dicts, sets, tuples)
- Nested configuration models
- Enums for type-safe values
"""

from enum import Enum

from tomlev import BaseConfigModel, TomlEv


class Environment(Enum):
    """Environment enum."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ConnectionPoolConfig(BaseConfigModel):
    """Database connection pool configuration."""

    min_size: int
    max_size: int
    timeout: int


class DatabaseConfig(BaseConfigModel):
    """Database configuration with nested pool config."""

    host: str
    port: int
    name: str
    user: str
    password: str
    connection_pool: ConnectionPoolConfig


class FeaturesConfig(BaseConfigModel):
    """Feature flags configuration."""

    new_ui: bool
    beta_api: bool
    experimental_cache: bool
    ai_assistant: bool


class APIConfig(BaseConfigModel):
    """API configuration."""

    version: str
    endpoints: list[str]
    allowed_methods: list[str]
    rate_limits: dict[str, int]


class SecurityConfig(BaseConfigModel):
    """Security configuration."""

    cors_origins: list[str]
    allowed_hosts: set[str]
    jwt_algorithm: str
    session_timeout: int


class MonitoringConfig(BaseConfigModel):
    """Monitoring configuration."""

    enabled: bool
    metrics: list[str]
    alert_thresholds: dict[str, float]
    coordinates: tuple[float, float]


class AppConfig(BaseConfigModel):
    """Main application configuration."""

    app_name: str
    environment: str

    database: DatabaseConfig
    features: FeaturesConfig
    api: APIConfig
    security: SecurityConfig
    monitoring: MonitoringConfig


def main() -> None:
    """Load and display advanced configuration."""
    # Load configuration (includes will be resolved automatically)
    config = TomlEv(AppConfig, "main.toml", ".env").validate()

    print("=" * 70)
    print("Advanced TomlEv Configuration Example")
    print("=" * 70)

    print(f"\nApp: {config.app_name}")
    print(f"Environment: {config.environment}")

    print("\n" + "-" * 70)
    print("Database Configuration (loaded from database.toml)")
    print("-" * 70)
    print(f"Host: {config.database.host}")
    print(f"Port: {config.database.port}")
    print(f"Database: {config.database.name}")
    print(f"User: {config.database.user}")
    print(f"Connection Pool: {config.database.connection_pool.min_size}-{config.database.connection_pool.max_size}")
    print(f"Pool Timeout: {config.database.connection_pool.timeout}s")

    print("\n" + "-" * 70)
    print("Feature Flags (loaded from features.toml)")
    print("-" * 70)
    print(f"New UI: {config.features.new_ui}")
    print(f"Beta API: {config.features.beta_api}")
    print(f"Experimental Cache: {config.features.experimental_cache}")
    print(f"AI Assistant: {config.features.ai_assistant}")

    print("\n" + "-" * 70)
    print("API Configuration")
    print("-" * 70)
    print(f"Version: {config.api.version}")
    print(f"Endpoints: {', '.join(config.api.endpoints)}")
    print(f"Allowed Methods: {', '.join(config.api.allowed_methods)}")
    print("Rate Limits:")
    for tier, limit in config.api.rate_limits.items():
        print(f"  {tier}: {limit} req/min")

    print("\n" + "-" * 70)
    print("Security Configuration")
    print("-" * 70)
    print(f"CORS Origins: {', '.join(config.security.cors_origins)}")
    print(f"Allowed Hosts (set): {', '.join(sorted(config.security.allowed_hosts))}")
    print(f"JWT Algorithm: {config.security.jwt_algorithm}")
    print(f"Session Timeout: {config.security.session_timeout}s")

    print("\n" + "-" * 70)
    print("Monitoring Configuration")
    print("-" * 70)
    print(f"Enabled: {config.monitoring.enabled}")
    print(f"Metrics: {', '.join(config.monitoring.metrics)}")
    print("Alert Thresholds:")
    for metric, threshold in config.monitoring.alert_thresholds.items():
        print(f"  {metric}: {threshold}%")
    print(f"Location: {config.monitoring.coordinates}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
