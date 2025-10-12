"""
MIT License

Copyright (c) 2025 Nick Bubelich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from os import environ
from pathlib import Path
from typing import Generic, TypeVar

from .__model__ import BaseConfigModel
from .constants import DEFAULT_ENV_FILE, DEFAULT_SEPARATOR, DEFAULT_TOML_FILE, TOMLEV_ENV_FILE, TOMLEV_TOML_FILE
from .env_loader import EnvDict
from .include_handler import expand_includes_dict
from .parser import ConfigDict, substitute_and_parse

__all__ = ["TomlEvAsync", "tomlev_async", "read_toml_async"]

T = TypeVar("T", bound=BaseConfigModel)

# Check if aiofiles is available
try:
    import aiofiles
    import aiofiles.os

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False


async def _read_file_async(file_path: str) -> str:
    """Read file content asynchronously.

    Args:
        file_path: Path to the file to read.

    Returns:
        File content as string.

    Raises:
        ImportError: If aiofiles is not installed.
    """
    if not AIOFILES_AVAILABLE:
        raise ImportError(
            "aiofiles is required for async file operations. Install it with: pip install aiofiles or uv add aiofiles"
        )

    async with aiofiles.open(file_path, mode="rt", encoding="utf8") as fp:
        return await fp.read()


async def read_env_file_async(file_path: str | None, strict: bool = True) -> EnvDict:
    """Read and parse environment variables from a .env file asynchronously.

    Args:
        file_path: Path to the .env file to read. If None or file doesn't exist, returns empty dict.
        strict: Whether to enforce strict mode validation for duplicate variables.

    Returns:
        Dictionary containing parsed environment variables.

    Raises:
        EnvironmentVariableError: In strict mode, when duplicate variables are found.
        ImportError: If aiofiles is not installed.
    """
    from .env_loader import read_env_file

    if not file_path:
        return {}

    # Check if file exists asynchronously
    if AIOFILES_AVAILABLE:
        if not await aiofiles.os.path.isfile(file_path):
            return {}
    else:
        if not Path(file_path).is_file():
            return {}

    # Read file asynchronously
    content = await _read_file_async(file_path)

    # Use synchronous parsing logic (minimal I/O impact)
    # We could refactor env_loader.py to separate parsing from reading,
    # but for now we'll use a simple approach
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf8") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = read_env_file(tmp_path, strict)
    finally:
        Path(tmp_path).unlink()

    return result


async def read_toml_async(file_path: str, env: EnvDict, strict: bool, separator: str = DEFAULT_SEPARATOR) -> ConfigDict:
    """Read and parse TOML file with environment variable substitution asynchronously.

    Args:
        file_path: Path to the TOML file to read.
        env: Dictionary of environment variables for substitution.
        strict: Whether to operate in strict mode for error handling.
        separator: Separator string for default values in environment variables.

    Returns:
        Dictionary of parsed TOML configuration with substituted values.

    Raises:
        FileNotFoundError: When the specified TOML file doesn't exist.
        EnvironmentVariableError: In strict mode, when referenced variables are undefined.
        ImportError: If aiofiles is not installed.
    """
    from .errors import EnvironmentVariableError

    # Read file asynchronously
    try:
        content: str = await _read_file_async(file_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"TOML file not found: {file_path}") from e
    except (OSError, IOError) as e:
        raise OSError(f"Error reading TOML file '{file_path}': {e}") from e

    # Perform substitution and parse (synchronous operations, minimal impact)
    try:
        toml = substitute_and_parse(content, env, strict, separator)
    except EnvironmentVariableError as e:
        # Add file context to environment variable errors
        errors = [(attr, f"{msg} (in file: {file_path})") for attr, msg in e.errors]
        raise EnvironmentVariableError(errors) from e
    except Exception as e:
        # Add file context to parsing errors
        raise ValueError(f"Error parsing TOML file '{file_path}': {e}") from e

    # Expand __include directives recursively (with async file reading)
    if toml and isinstance(toml, dict):
        # Note: expand_includes_dict is synchronous and uses sync I/O
        # For full async support, we'd need to refactor include_handler.py
        # For now, we'll use the sync version
        expand_includes_dict(
            toml,
            Path(file_path).parent,
            env,
            strict,
            separator,
            seen={Path(file_path).resolve()},
            cache={},
            substitute_and_parse_func=substitute_and_parse,
        )
        return toml

    return {}


class TomlEvAsync(Generic[T]):
    """Async version of TomlEv for loading configuration from files asynchronously.

    This is useful for applications that use async I/O and want to load
    configuration files without blocking the event loop.

    Example:
        ```python
        import asyncio
        from tomlev.async_support import TomlEvAsync

        async def main():
            loader = await TomlEvAsync.create(AppConfig, "env.toml", ".env")
            config = loader.validate()
            print(f"Server: {config.host}:{config.port}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        cls: type[T],
        toml_vars: ConfigDict,
        env_vars: EnvDict,
        strict: bool,
    ) -> None:
        """Internal constructor. Use TomlEvAsync.create() instead."""
        self.__cls = cls
        self.__toml_vars = toml_vars
        self.__vars = env_vars
        self.__strict = strict

        # Create the model instance
        self.__model = cls(**toml_vars)

    @classmethod
    async def create(
        cls,
        config_cls: type[T],
        toml_file: str | None = None,
        env_file: str | None = None,
        strict: bool = True,
        include_environment: bool = True,
    ) -> TomlEvAsync[T]:
        """Create a TomlEvAsync instance asynchronously.

        Args:
            config_cls: Configuration model class that extends BaseConfigModel.
            toml_file: Path to the TOML configuration file.
            env_file: Path to the .env file for environment variables.
            strict: Whether to enforce strict mode validation.
            include_environment: Whether to include system environment variables.

        Returns:
            TomlEvAsync instance with loaded configuration.

        Raises:
            ConfigValidationError: When configuration validation fails.
            FileNotFoundError: When the specified TOML file doesn't exist.
            ImportError: If aiofiles is not installed.
        """
        # Determine file paths from environment variables or defaults
        if toml_file is None:
            toml_file = environ.get(TOMLEV_TOML_FILE, DEFAULT_TOML_FILE)
        if env_file is None:
            env_file = environ.get(TOMLEV_ENV_FILE, DEFAULT_ENV_FILE)

        # Read environment
        env_vars: EnvDict = dict(environ) if include_environment else {}

        # Read .env file asynchronously
        dotenv: ConfigDict = await read_env_file_async(env_file, strict)
        env_vars.update(dotenv)

        # Read TOML file asynchronously
        toml_vars: ConfigDict = await read_toml_async(toml_file, env_vars, strict)

        return cls(config_cls, toml_vars, env_vars, strict)

    @property
    def environ(self) -> EnvDict:
        """Get the combined environment variables mapping."""
        return self.__vars

    @property
    def strict(self) -> bool:
        """Get the current strict mode setting."""
        return self.__strict

    @property
    def raw(self) -> ConfigDict:
        """Return the parsed TOML configuration dict after substitutions."""
        return dict(self.__toml_vars)

    def validate(self) -> T:
        """Validate and return the loaded configuration."""
        return self.__model


async def tomlev_async(
    cls: type[T],
    toml_file: str | None = None,
    env_file: str | None = None,
    strict: bool = True,
    include_environment: bool = True,
) -> T:
    """Async convenience function to load and validate configuration in one step.

    This is the async equivalent of tomlev(). Use this in async contexts
    when you want to load configuration files without blocking.

    Args:
        cls: Configuration model class that extends BaseConfigModel.
        toml_file: Path to the TOML configuration file.
        env_file: Path to the .env file for environment variables.
        strict: Whether to enforce strict mode validation.
        include_environment: Whether to include system environment variables.

    Returns:
        The validated configuration model instance.

    Raises:
        ConfigValidationError: When configuration validation fails.
        FileNotFoundError: When the specified TOML file doesn't exist.
        ImportError: If aiofiles is not installed.

    Example:
        ```python
        import asyncio
        from tomlev.async_support import tomlev_async

        async def main():
            config = await tomlev_async(AppConfig, "env.toml", ".env")
            print(f"Server: {config.host}:{config.port}")

        asyncio.run(main())
        ```
    """
    loader = await TomlEvAsync.create(cls, toml_file, env_file, strict, include_environment)
    return loader.validate()
