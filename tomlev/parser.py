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

import io
from functools import lru_cache
from pathlib import Path
from tomllib import loads as toml_loads
from typing import Any, TypeAlias

from .constants import DEFAULT_SEPARATOR
from .env_loader import EnvDict
from .errors import EnvironmentVariableError
from .include_handler import expand_includes_dict
from .patterns import RE_PATTERN

__all__ = ["ConfigDict", "read_toml", "substitute_and_parse"]

# Type aliases for clarity
ConfigDict: TypeAlias = dict[str, Any]


@lru_cache(maxsize=32)
def _read_file_cached(file_path: str) -> str:
    """Read file content with caching to avoid repeated disk I/O.

    Args:
        file_path: Path to the file to read.

    Returns:
        File content as string.
    """
    with io.open(file_path, mode="rt", encoding="utf8") as fp:
        return fp.read()


def substitute_and_parse(content: str, env: EnvDict, strict: bool, separator: str = DEFAULT_SEPARATOR) -> ConfigDict:
    """Substitute environment variables in content and parse TOML.

    Handles escapes (e.g., "$$" and "$1") and default syntax using the
    configured separator.

    Args:
        content: TOML content string with environment variable placeholders.
        env: Dictionary of environment variables for substitution.
        strict: Whether to operate in strict mode for error handling.
        separator: Separator string for default values in environment variables.

    Returns:
        Dictionary of parsed TOML configuration with substituted values.

    Raises:
        EnvironmentVariableError: In strict mode, when referenced variables are undefined.
    """
    # not found variables
    not_found_variables = set()

    # substitutions dictionary
    substitutions: dict[str, str] = {}

    # Build list of content segments for efficient string building
    segments: list[tuple[int, int, str]] = []  # (start, end, replacement)

    # iterate over findings
    for entry in RE_PATTERN.finditer(content):
        groups = entry.groupdict()

        # replace
        variable: str | None = None
        default: str | None = None
        replace: str | None = None

        match groups:
            case {"named": name, "named_default": def_val} if name:
                variable = name
                default = def_val
            case {"braced": name, "braced_default": def_val} if name:
                variable = name
                default = def_val
            case {"escaped": esc_val} if esc_val:
                span = entry.span()
                pref = groups.get("pref") or ""
                post = groups.get("post") or ""
                replacement = f"{pref}{esc_val}{post}"
                segments.append((span[0], span[1], replacement))
                continue

        if variable is not None:
            if variable in env:
                replace = env[variable]
            elif variable not in env and default is not None:
                replace = default
            else:
                not_found_variables.add(variable)

        if replace is not None and variable is not None:
            search = "${" if groups["braced"] else "$"
            search += variable
            if default is not None:
                search += separator + default
            search += "}" if groups["braced"] else ""
            substitutions[search] = replace

    if strict and not_found_variables:
        raise EnvironmentVariableError.missing_variables(list(not_found_variables))

    # Apply escape replacements efficiently using segments
    if segments:
        result_parts: list[str] = []
        last_end: int = 0
        for start, end, replacement in segments:
            result_parts.append(content[last_end:start])
            # Replacement is always str for escaped values, never None in practice
            if replacement is not None:
                result_parts.append(replacement)
            last_end = end
        result_parts.append(content[last_end:])
        content = "".join(result_parts)

    # Apply variable substitutions (single-pass, longest first to avoid partial replacements)
    for search in sorted(substitutions, key=len, reverse=True):
        content = content.replace(search, substitutions[search])

    # Parse TOML
    toml = toml_loads(content)
    if toml and isinstance(toml, dict):
        return toml
    return {}


def read_toml(file_path: str, env: EnvDict, strict: bool, separator: str = DEFAULT_SEPARATOR) -> ConfigDict:
    """Read and parse TOML file with environment variable substitution.

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
    """
    # read file (with caching for repeated reads)
    try:
        content: str = _read_file_cached(file_path)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"TOML file not found: {file_path}") from e
    except (OSError, IOError) as e:
        raise OSError(f"Error reading TOML file '{file_path}': {e}") from e

    # Perform substitution and parse
    try:
        toml = substitute_and_parse(content, env, strict, separator)
    except EnvironmentVariableError as e:
        # Add file context to environment variable errors
        errors = [(attr, f"{msg} (in file: {file_path})") for attr, msg in e.errors]
        raise EnvironmentVariableError(errors) from e
    except Exception as e:
        # Add file context to parsing errors
        raise ValueError(f"Error parsing TOML file '{file_path}': {e}") from e

    # Expand __include directives recursively
    if toml and isinstance(toml, dict):
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
