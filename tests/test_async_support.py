"""
Comprehensive tests for async I/O support in TomlEv.

This module tests all async functionality including:
- tomlev_async() convenience function
- TomlEvAsync class and its methods
- Async file operations
- Error handling in async mode
- Integration with sync behavior
"""

from __future__ import annotations

import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch

import pytest

from tomlev import BaseConfigModel
from tomlev.async_support import TomlEvAsync, read_env_file_async, read_toml_async, tomlev_async
from tomlev.errors import ConfigValidationError, EnvironmentVariableError


# Test configuration models (reused from test_simple.py)
class SelectEnum(Enum):
    """Enum for selection."""

    ONE = "one"
    TWO = "two"
    THREE = "three"


class StripeConfig(BaseConfigModel):
    """Configuration for Stripe payment processing."""

    key: str
    domain: str
    product_prd1_price: str
    product_prd1_redirect: str


class DatabaseConfig(BaseConfigModel):
    """Database connection configuration."""

    uri: str
    host: str
    port: int
    user: str
    password: str
    name: str
    queries: dict[str, Any]


class RedisConfig(BaseConfigModel):
    """Redis cache configuration."""

    host: str
    port: int
    keys: list[str]
    nums: list[int]
    atts: list[dict[str, Any]]
    weight: int
    mass: float


class IncludeNested(BaseConfigModel):
    """Nested configuration for include_other_toml."""

    include_param: str
    nested: dict


class SimpleConfig(BaseConfigModel):
    """Main application configuration."""

    debug: bool
    environment: str
    temp: float
    stripe: StripeConfig
    database: DatabaseConfig
    redis: RedisConfig
    select_literal: Literal["one", "two", "three"]
    select_enum: SelectEnum
    include_other_toml: IncludeNested
    test_set: set[str]
    test_tuple: tuple[str, int, float]


class BasicConfig(BaseConfigModel):
    """Simple configuration for basic tests."""

    host: str
    port: int
    debug: bool


# =============================================================================
# Basic Async Operations Tests
# =============================================================================


@pytest.mark.asyncio
async def test_tomlev_async_convenience_function():
    """Test tomlev_async() convenience function with real files."""
    config = await tomlev_async(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Verify core values
    assert config.debug is False
    assert config.environment == "develop"
    assert config.temp == -20.5

    # Verify it's a proper SimpleConfig instance
    assert isinstance(config, SimpleConfig)

    # Verify nested structures
    assert config.database.host == "localhost"
    assert config.database.port == 5432
    assert config.redis.port == 6379


@pytest.mark.asyncio
async def test_tomlev_async_with_env_substitution():
    """Test environment variable substitution in async mode."""
    config = await tomlev_async(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Verify substitutions from .env file
    assert config.database.user == "UserUser"
    assert config.database.password == "PasswordPassword"
    assert config.stripe.key == "sk-test-00000"


@pytest.mark.asyncio
async def test_tomlev_async_default_files():
    """Test tomlev_async() with default file paths from environment variables."""
    # Set environment variables for default paths
    os.environ["TOMLEV_TOML_FILE"] = "tests/envs/env.simple.toml"
    os.environ["TOMLEV_ENV_FILE"] = "tests/envs/.env.simple"

    try:
        # Call without explicit file paths
        config = await tomlev_async(SimpleConfig)

        # Verify it loaded correctly
        assert config.debug is False
        assert config.environment == "develop"
    finally:
        # Clean up environment variables
        os.environ.pop("TOMLEV_TOML_FILE", None)
        os.environ.pop("TOMLEV_ENV_FILE", None)


@pytest.mark.asyncio
async def test_tomlev_async_strict_mode_enabled():
    """Test async loading with strict mode enabled (default)."""
    # Create a TOML file with an undefined variable
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "${UNDEFINED_VAR}"\n')
        f.write("port = 8080\n")
        f.write("debug = true\n")
        toml_path = f.name

    try:
        # Should raise error in strict mode
        with pytest.raises((EnvironmentVariableError, ConfigValidationError, ValueError)):
            await tomlev_async(BasicConfig, toml_path, None, strict=True)
    finally:
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_tomlev_async_strict_mode_disabled():
    """Test async loading with strict mode disabled."""
    # Create a TOML file with an undefined variable but default value
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "${UNDEFINED_VAR|-localhost}"\n')
        f.write("port = 8080\n")
        f.write("debug = true\n")
        toml_path = f.name

    try:
        # Should work in non-strict mode
        config = await tomlev_async(BasicConfig, toml_path, None, strict=False)
        assert config.host == "localhost"
        assert config.port == 8080
    finally:
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_tomlev_async_frozen_config():
    """Test that frozen configs work with async loading."""

    class FrozenConfig(BaseConfigModel, frozen=True):
        host: str
        port: int

    # Create test files
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "localhost"\n')
        f.write("port = 8080\n")
        toml_path = f.name

    try:
        config = await tomlev_async(FrozenConfig, toml_path, None)

        # Verify it loaded correctly
        assert config.host == "localhost"
        assert config.port == 8080

        # Verify it's frozen
        with pytest.raises(AttributeError):
            config.port = 9000
    finally:
        Path(toml_path).unlink()


# =============================================================================
# TomlEvAsync Class Tests
# =============================================================================


@pytest.mark.asyncio
async def test_tomlev_async_create_factory():
    """Test TomlEvAsync.create() factory method."""
    loader = await TomlEvAsync.create(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Verify loader was created
    assert loader is not None
    assert isinstance(loader, TomlEvAsync)

    # Verify config can be validated
    config = loader.validate()
    assert isinstance(config, SimpleConfig)


@pytest.mark.asyncio
async def test_tomlev_async_environ_property():
    """Test TomlEvAsync.environ property."""
    loader = await TomlEvAsync.create(
        SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple", include_environment=True
    )

    # Get environ dict
    env_vars = loader.environ

    # Verify it contains .env values
    assert "DB_USER" in env_vars
    assert env_vars["DB_USER"] == "UserUser"

    # Verify it's a dict
    assert isinstance(env_vars, dict)


@pytest.mark.asyncio
async def test_tomlev_async_strict_property():
    """Test TomlEvAsync.strict property."""
    # Test with strict=True
    loader_strict = await TomlEvAsync.create(
        SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple", strict=True
    )
    assert loader_strict.strict is True

    # Test with strict=False
    loader_non_strict = await TomlEvAsync.create(
        SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple", strict=False
    )
    assert loader_non_strict.strict is False


@pytest.mark.asyncio
async def test_tomlev_async_raw_property():
    """Test TomlEvAsync.raw property."""
    loader = await TomlEvAsync.create(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Get raw dict
    raw_dict = loader.raw

    # Verify it's a dict with expected keys
    assert isinstance(raw_dict, dict)
    assert "debug" in raw_dict
    assert "environment" in raw_dict
    assert "database" in raw_dict

    # Verify values are substituted (raw dict keeps string values from TOML)
    assert raw_dict["debug"] == "False"  # TOML parser preserves case
    assert raw_dict["environment"] == "develop"


@pytest.mark.asyncio
async def test_tomlev_async_validate_method():
    """Test TomlEvAsync.validate() method."""
    loader = await TomlEvAsync.create(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Validate
    config = loader.validate()

    # Verify it returns a proper config instance
    assert isinstance(config, SimpleConfig)
    assert config.debug is False

    # Verify we can call validate multiple times
    config2 = loader.validate()
    assert config2 is config  # Should return the same instance


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
async def test_async_missing_toml_file():
    """Test FileNotFoundError when TOML file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        await tomlev_async(BasicConfig, "nonexistent_file.toml", None)


@pytest.mark.asyncio
async def test_async_invalid_toml_syntax():
    """Test ValueError for invalid TOML syntax."""
    # Create a TOML file with invalid syntax
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("invalid toml syntax = [[[")
        toml_path = f.name

    try:
        with pytest.raises((ValueError, Exception)):
            await tomlev_async(BasicConfig, toml_path, None)
    finally:
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_async_missing_env_variable_strict():
    """Test error when env variable is missing in strict mode."""
    # Create TOML with undefined variable
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "${MISSING_HOST}"\n')
        f.write("port = 8080\n")
        f.write("debug = true\n")
        toml_path = f.name

    try:
        with pytest.raises((EnvironmentVariableError, ConfigValidationError, ValueError)):
            await tomlev_async(BasicConfig, toml_path, None, strict=True)
    finally:
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_async_missing_env_file_ok():
    """Test that missing .env file is OK and doesn't raise error."""
    # Create simple TOML without variables
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "localhost"\n')
        f.write("port = 8080\n")
        f.write("debug = true\n")
        toml_path = f.name

    try:
        # Should work fine with missing .env file
        config = await tomlev_async(BasicConfig, toml_path, "nonexistent.env")
        assert config.host == "localhost"
    finally:
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_async_unreadable_file():
    """Test OSError for file permission issues."""
    # Create a TOML file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "localhost"\n')
        toml_path = f.name

    try:
        # Make it unreadable (Unix only)
        if os.name != "nt":  # Skip on Windows
            os.chmod(toml_path, 0o000)
            with pytest.raises((OSError, PermissionError, FileNotFoundError)):
                await tomlev_async(BasicConfig, toml_path, None)
    finally:
        # Restore permissions and delete
        if os.name != "nt":
            os.chmod(toml_path, 0o644)
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_async_missing_aiofiles_import():
    """Test ImportError when aiofiles is not installed."""
    # Mock aiofiles as unavailable
    with patch("tomlev.async_support.AIOFILES_AVAILABLE", False):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('host = "localhost"\n')
            toml_path = f.name

        try:
            with pytest.raises(ImportError, match="aiofiles is required"):
                await tomlev_async(BasicConfig, toml_path, None)
        finally:
            Path(toml_path).unlink()


# =============================================================================
# File Operations Tests
# =============================================================================


@pytest.mark.asyncio
async def test_read_env_file_async_success():
    """Test async .env file reading."""
    # Use existing .env.simple file
    env_dict = await read_env_file_async("tests/envs/.env.simple", strict=True)

    # Verify it loaded
    assert isinstance(env_dict, dict)
    assert "DB_USER" in env_dict
    assert env_dict["DB_USER"] == "UserUser"


@pytest.mark.asyncio
async def test_read_env_file_async_none_path():
    """Test that None path returns empty dict."""
    env_dict = await read_env_file_async(None, strict=True)
    assert env_dict == {}


@pytest.mark.asyncio
async def test_read_toml_async_success():
    """Test async TOML file reading."""
    # Create simple TOML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('host = "localhost"\n')
        f.write("port = 8080\n")
        toml_path = f.name

    try:
        toml_dict = await read_toml_async(toml_path, {}, strict=True)

        # Verify it loaded
        assert isinstance(toml_dict, dict)
        assert toml_dict["host"] == "localhost"
        assert toml_dict["port"] == 8080  # TOML parser converts to int
    finally:
        Path(toml_path).unlink()


@pytest.mark.asyncio
async def test_read_toml_async_with_includes():
    """Test async TOML reading with __include directives."""
    # Use existing file with includes
    env_dict = await read_env_file_async("tests/envs/.env.simple", strict=True)
    toml_dict = await read_toml_async("tests/envs/env.simple.toml", env_dict, strict=True)

    # Verify includes were processed
    assert isinstance(toml_dict, dict)
    assert "include_other_toml" in toml_dict


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_async_same_result_as_sync():
    """Test that async loading produces the same result as sync loading."""
    from tomlev import tomlev

    # Load async
    async_config = await tomlev_async(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Load sync
    sync_config = tomlev(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Compare results
    assert async_config.debug == sync_config.debug
    assert async_config.environment == sync_config.environment
    assert async_config.temp == sync_config.temp
    assert async_config.database.host == sync_config.database.host
    assert async_config.database.port == sync_config.database.port
    assert async_config.redis.port == sync_config.redis.port


@pytest.mark.asyncio
async def test_async_concurrent_loading():
    """Test multiple concurrent async loads."""
    import asyncio

    # Load same config 5 times concurrently
    tasks = [tomlev_async(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple") for _ in range(5)]

    # Wait for all to complete
    configs = await asyncio.gather(*tasks)

    # Verify all loaded successfully
    assert len(configs) == 5
    for config in configs:
        assert isinstance(config, SimpleConfig)
        assert config.debug is False
        assert config.environment == "develop"


@pytest.mark.asyncio
async def test_async_complex_config():
    """Test async loading with complex configuration (all types)."""
    config = await tomlev_async(SimpleConfig, "tests/envs/env.simple.toml", "tests/envs/.env.simple")

    # Verify all complex types
    assert config.database.queries["get_version"] == """SELECT version();"""
    assert config.redis.keys == ["one", "two", "three"]
    assert config.redis.nums == [10, 12, 99]
    assert config.redis.atts == [{"name": "one", "age": 10}, {"name": "two", "age": 12}]
    assert config.select_literal == "one"
    assert config.select_enum == SelectEnum.ONE
    assert type(config.test_set) is set
    assert type(config.test_tuple) is tuple
    assert config.test_tuple == ("one", 1, 10.5)
