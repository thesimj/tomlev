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

import io
import re
from os import environ
from os.path import expandvars
from pathlib import Path
from tomllib import loads as toml_loads
from typing import Any, Generic, TypeAlias, TypeVar

from tomlev.__model__ import BaseConfigModel, ConfigValidationError

__version__ = "1.0.1"

T = TypeVar("T", bound=BaseConfigModel)

# Type aliases for clarity
ConfigDict: TypeAlias = dict[str, Any]
EnvDict: TypeAlias = dict[str, Any]

# pattern to remove comments
RE_COMMENTS = re.compile(r"(^#.*\n)", re.MULTILINE | re.UNICODE | re.IGNORECASE)

# pattern to read .env file
RE_DOT_ENV = re.compile(
    r"^(?!\d+)(?P<name>[\w\-\.]+)\=[\"\']?(?P<value>(.*?))[\"\']?$",
    re.MULTILINE | re.UNICODE | re.IGNORECASE,
)

# pattern to extract env variables
RE_PATTERN = re.compile(
    r"(?P<pref>[\"\'])?"
    r"(\$(?:(?P<escaped>(\$|\d+))|"
    r"{(?P<braced>(.*?))(\|-(?P<braced_default>.*?))?}|"
    r"(?P<named>[\w\-\.]+)(\|(?P<named_default>.*))?))"
    r"(?P<post>[\"\'])?",
    re.MULTILINE | re.UNICODE | re.IGNORECASE | re.VERBOSE,
)


class TomlEv(Generic[T]):
    """Type-safe TOML configuration loader with environment variable substitution.

    TomlEv provides a convenient way to load configuration from TOML files
    while supporting environment variable substitution using ${VAR|-default} syntax.
    It automatically validates and converts types based on the provided configuration model.

    Args:
        Generic[T]: The configuration model type that extends BaseConfigModel.

    Attributes:
        TOMLEV_STRICT_DISABLE: Environment variable name to disable strict mode globally.
        DEFAULT_ENV_TOML_FILE: Default TOML configuration file name.
        DEFAULT_ENV_FILE: Default environment file name.

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

    TOMLEV_STRICT_DISABLE: str = "TOMLEV_STRICT_DISABLE"
    DEFAULT_ENV_TOML_FILE: str = "env.toml"
    DEFAULT_ENV_FILE: str = ".env"

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
            ValueError: In strict mode, when environment variables are undefined
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
            (environ["TOMLEV_STRICT_DISABLE"].lower() not in {"true", "1", "yes", "y", "on", "t"})
            if "TOMLEV_STRICT_DISABLE" in environ
            else strict
        )

        # read .env files and update environment variables
        self.__dotenv: ConfigDict = self.__read_envfile(env_file, self.__strict)

        # set environ with dot env variables
        self.__vars.update(self.__dotenv)

        # read toml files
        self.__toml_vars: ConfigDict = self.__read_toml(toml_file, self.__vars, self.__strict)

        self.__cls = cls(**self.__toml_vars)

    @staticmethod
    def __read_envfile(file_path: str | None, strict: bool = True) -> ConfigDict:
        """Read and parse environment variables from a .env file.

        Args:
            file_path: Path to the .env file to read, or None if no file.
            strict: Whether to operate in strict mode for error handling.

        Returns:
            Dictionary of environment variable names to values.
        """
        config: ConfigDict = {}
        defined: set[str] = set()

        # check if a file exists in filesystem
        if file_path and Path(file_path).is_file():
            with io.open(file_path, mode="rt", encoding="utf8") as fp:
                content: str = expandvars(fp.read())

            # iterate over findings
            for entry in RE_DOT_ENV.finditer(content):
                name = entry.group("name")
                value = entry.group("value")

                # check double definition
                if name in config:
                    defined.add(name)

                # set config
                config[name] = value

        # strict mode - maintain backward compatibility for error messages
        if strict and defined:
            duplicate_vars = sorted(defined)
            raise ConfigValidationError(
                [
                    (
                        "environment_variables",
                        "Strict mode enabled, variables "
                        + ", ".join(["$" + v for v in duplicate_vars])
                        + " defined several times!",
                    )
                ]
            )

        return config

    @staticmethod
    def __read_toml(file_path: str, env: EnvDict, strict: bool, separator: str = "|-") -> ConfigDict:
        """Read and parse TOML file with environment variable substitution.

        Args:
            file_path: Path to the TOML file to read.
            env: Dictionary of environment variables for substitution.
            strict: Whether to operate in strict mode for error handling.
            separator: Separator string for default values in environment variables.

        Returns:
            Dictionary of parsed TOML configuration with substituted values.
        """
        # read file
        with io.open(file_path, mode="rt", encoding="utf8") as fp:
            content: str = fp.read()

        # remove all comments
        content = RE_COMMENTS.sub("", content)

        # not found variables
        not_found_variables = set()

        # change dictionary
        replaces: dict[str, str] = {}

        shifting = 0

        # iterate over findings
        for entry in RE_PATTERN.finditer(content):
            groups = entry.groupdict()

            # replace
            variable: str | None = None
            default: str | None = None
            replace: str | None = None

            # Use structural pattern matching for better readability
            match groups:
                case {"named": name, "named_default": def_val} if name:
                    variable = name
                    default = def_val
                case {"braced": name, "braced_default": def_val} if name:
                    variable = name
                    default = def_val
                case {"escaped": esc_val} if esc_val and "$" in esc_val:
                    span = entry.span()
                    content = content[: span[0] + shifting] + esc_val + content[span[1] + shifting :]
                    # Added shifting since every time we update content, we are
                    # changing the original groups spans
                    shifting += len(esc_val) - (span[1] - span[0])

            if variable is not None:
                if variable in env:
                    replace = env[variable]
                elif variable not in env and default is not None:
                    replace = default
                else:
                    not_found_variables.add(variable)

            if replace is not None and variable is not None:
                # build match
                search = "${" if groups["braced"] else "$"
                search += variable
                if default is not None:
                    search += separator + default
                search += "}" if groups["braced"] else ""

                # store findings
                replaces[search] = replace

        # strict mode - maintain backward compatibility for error messages
        if strict and not_found_variables:
            missing_vars = sorted(not_found_variables)
            raise ConfigValidationError(
                [
                    (
                        "environment_variables",
                        "Strict mode enabled, variables "
                        + ", ".join(["$" + v for v in missing_vars])
                        + " are not defined!",
                    )
                ]
            )

        # replace finding with their respective values
        for replace in sorted(replaces, reverse=True):
            content = content.replace(replace, replaces[replace])

        # load proper content
        toml = toml_loads(content)

        # if contains something
        if toml and isinstance(toml, dict):
            return toml

        return {}

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
