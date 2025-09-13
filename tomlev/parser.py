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
                content = content[: span[0] + shifting] + replacement + content[span[1] + shifting :]
                shifting += len(replacement) - (span[1] - span[0])

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
            replaces[search] = replace

    if strict and not_found_variables:
        raise EnvironmentVariableError.missing_variables(list(not_found_variables))

    # Apply replacements
    for replace in sorted(replaces, reverse=True):
        content = content.replace(replace, replaces[replace])

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
    # read file
    with io.open(file_path, mode="rt", encoding="utf8") as fp:
        content: str = fp.read()

    # Perform substitution and parse
    toml = substitute_and_parse(content, env, strict, separator)

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
