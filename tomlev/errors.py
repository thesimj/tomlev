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

from typing import TypeAlias

__all__ = [
    "ConfigError",
    "ConfigValidationError",
    "EnvironmentVariableError",
    "IncludeError",
    "TypeConversionError",
]

# Type aliases for clarity
ConfigError: TypeAlias = tuple[str, str]  # (attribute, error_message)


class ConfigValidationError(Exception):
    """Exception raised when configuration model validation fails.

    This exception is raised when one or more configuration attributes
    fail validation during the model initialization process.

    Attributes:
        errors: List of tuples containing (attribute_name, error_message) pairs.

    Example:
        ```python
        try:
            config = MyConfig(invalid_data)
        except ConfigValidationError as e:
            for attr, msg in e.errors:
                print(f"Error in {attr}: {msg}")
        ```
    """

    def __init__(self, errors: list[ConfigError]) -> None:
        """Initialize the validation error.

        Args:
            errors: List of configuration errors as (attribute, message) tuples.
        """
        self.errors = errors
        error_messages = [f"'{attr}': {msg}" for attr, msg in errors]
        super().__init__(f"Configuration validation failed: {'; '.join(error_messages)}")


class EnvironmentVariableError(ConfigValidationError):
    """Exception raised for environment variable related errors."""

    @classmethod
    def missing_variables(cls, variables: list[str]) -> EnvironmentVariableError:
        """Create error for missing environment variables."""
        missing_vars = ", ".join(["$" + v for v in sorted(variables)])
        return cls([("environment_variables", f"Strict mode enabled, variables {missing_vars} are not defined!")])

    @classmethod
    def duplicate_variables(cls, variables: list[str]) -> EnvironmentVariableError:
        """Create error for duplicate environment variables."""
        duplicate_vars = ", ".join(["$" + v for v in sorted(variables)])
        return cls(
            [("environment_variables", f"Strict mode enabled, variables {duplicate_vars} defined several times!")]
        )


class IncludeError(ConfigValidationError):
    """Exception raised for include directive related errors."""

    @classmethod
    def invalid_type(cls) -> IncludeError:
        """Create error for invalid include type."""
        return cls([("include", "__include must be a string or list of strings")])

    @classmethod
    def cycle_detected(cls, path: str) -> IncludeError:
        """Create error for include cycle."""
        return cls([("include", f"Include cycle detected at {path}")])

    @classmethod
    def file_not_found(cls, path: str) -> IncludeError:
        """Create error for missing include file."""
        return cls([("include", f"Included TOML not found: {path}")])


class TypeConversionError(ConfigValidationError):
    """Exception raised for type conversion failures."""

    @classmethod
    def invalid_type(cls, attr: str, expected_type: str, actual_type: str) -> TypeConversionError:
        """Create error for invalid type conversion."""
        return cls([(attr, f"Expected {expected_type}, got {actual_type}")])

    @classmethod
    def invalid_literal(cls, attr: str, value: str, allowed: list[str]) -> TypeConversionError:
        """Create error for invalid literal value."""
        allowed_str = ", ".join(str(v) for v in allowed)
        return cls([(attr, f"Value {value!r} not in allowed Literal[{allowed_str}]")])

    @classmethod
    def invalid_enum(cls, attr: str, value: str, enum_name: str) -> TypeConversionError:
        """Create error for invalid enum value."""
        return cls([(attr, f"Invalid value {value!r} for enum {enum_name}")])
