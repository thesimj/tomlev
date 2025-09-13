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
from typing import Generic, TypeVar

from .__model__ import BaseConfigModel
from .cli import main as cli_main
from .constants import DEFAULT_ENV_FILE, DEFAULT_ENV_TOML_FILE, TOMLEV_STRICT_DISABLE, VERSION
from .env_loader import EnvDict, read_env_file
from .parser import ConfigDict, read_toml

__version__ = VERSION

T = TypeVar("T", bound=BaseConfigModel)


class TomlEv(Generic[T]):
    """Type-safe TOML configuration loader with environment variable substitution.

    TomlEv provides a convenient way to load configuration from TOML files
    while supporting environment variable substitution using ${VAR|-default} syntax.
    It automatically validates and converts types based on the provided configuration model.

    Args:
        Generic[T]: The configuration model type that extends BaseConfigModel.

    Example:
        ```python
        class AppConfig(BaseConfigModel):
            host: str
            port: int
            debug: bool

        # Load configuration with automatic validation
        config = TomlEv(AppConfig, "env.toml", ".env").validate()

        # Access type-safe configuration
        print(f"Server running on {config.host}:{config.port}")
        ```
    """

    # variables
    __vars: EnvDict
    __strict: bool
    __cls: T

    def __init__(
        self,
        cls: type[T],
        toml_file: str = DEFAULT_ENV_TOML_FILE,
        env_file: str | None = DEFAULT_ENV_FILE,
        strict: bool = True,
        include_environment: bool = True,
    ) -> None:
        """Initialize TomlEv configuration loader.

        Args:
            cls: Configuration model class that extends BaseConfigModel.
            toml_file: Path to the TOML configuration file. Defaults to "env.toml".
            env_file: Path to the .env file for environment variables.
                     Set to None to skip loading .env file. Defaults to ".env".
            strict: Whether to enforce strict mode validation. When True, raises
                   errors for undefined variables or duplicates. Defaults to True.
            include_environment: Whether to include system environment variables.
                               Defaults to True.

        Raises:
            ConfigValidationError: In strict mode, when environment variables are undefined
                                 or when duplicate variables are found in .env file.
            FileNotFoundError: When the specified TOML file doesn't exist.

        Note:
            Strict mode can be globally disabled by setting the environment
            variable TOMLEV_STRICT_DISABLE to "true", "1", "yes", "y", or "on".
        """
        # read environment
        self.__vars: EnvDict = dict(environ) if include_environment else {}

        # set strict mode to false if "TOMLEV_STRICT_DISABLE" presents in env else use "strict" from the function
        self.__strict = (
            (environ[TOMLEV_STRICT_DISABLE].lower() not in {"true", "1", "yes", "y", "on", "t"})
            if TOMLEV_STRICT_DISABLE in environ
            else strict
        )

        # read .env files and update environment variables
        self.__dotenv: ConfigDict = read_env_file(env_file, self.__strict)

        # set environ with dot env variables
        self.__vars.update(self.__dotenv)

        # read toml files
        self.__toml_vars: ConfigDict = read_toml(toml_file, self.__vars, self.__strict)

        self.__cls = cls(**self.__toml_vars)

    @property
    def environ(self) -> EnvDict:
        """Get the combined environment variables mapping.

        Returns a dictionary containing both system environment variables
        and variables loaded from the .env file.

        Returns:
            Dictionary containing all environment variables available to the configuration.
        """
        return self.__vars

    @property
    def strict(self) -> bool:
        """Get the current strict mode setting.

        Returns:
            True if strict mode is enabled, False otherwise.
        """
        return self.__strict

    @property
    def raw(self) -> ConfigDict:
        """Return the parsed TOML configuration dict after substitutions.

        Useful for introspection or serialization without creating a model.
        """
        return dict(self.__toml_vars)

    def validate(self) -> T:
        """Validate and return the loaded configuration.

        Returns:
            The validated configuration model instance with all values
            properly typed and converted.

        Raises:
            ConfigValidationError: When configuration validation fails due to
                                  type conversion errors or missing required fields.
        """
        return self.__cls


def main(argv: list[str] | None = None) -> int:
    """TomlEv CLI entry point.

    Commands:
    - validate: Validate TOML file with env substitution (schema-less).

    Args:
        argv: Command line arguments. If None, uses sys.argv.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    return cli_main(argv)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
