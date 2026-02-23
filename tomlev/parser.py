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
import re
from functools import lru_cache
from pathlib import Path
from tomllib import loads as toml_loads
from typing import Any, TypeAlias

from .constants import DEFAULT_SEPARATOR
from .env_loader import EnvDict
from .errors import EnvironmentVariableError
from .include_handler import expand_includes_dict

__all__ = ["ConfigDict", "read_toml", "substitute_and_parse"]

# Type aliases for clarity
ConfigDict: TypeAlias = dict[str, Any]
SubstitutionSegment: TypeAlias = tuple[int, int, str]
SubstitutionScanResult: TypeAlias = tuple[dict[str, str], list[SubstitutionSegment], set[str]]


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


def _apply_substitutions_batch(content: str, substitutions: dict[str, str]) -> str:
    """Apply multiple substitutions in a single pass using regex for better performance.

    This is significantly faster than multiple str.replace() calls when there are
    many substitutions to perform.

    Args:
        content: The content string to perform substitutions on.
        substitutions: Dictionary mapping search strings to replacement strings.

    Returns:
        Content with all substitutions applied.
    """
    if not substitutions:
        return content

    # Sort by length (longest first) to avoid partial replacements
    sorted_keys = sorted(substitutions.keys(), key=len, reverse=True)

    # Create a regex pattern that matches any of the search strings
    # Escape each key to handle special regex characters
    pattern = "|".join(re.escape(key) for key in sorted_keys)

    # Perform single-pass replacement using a lambda that looks up the matched text
    return re.sub(pattern, lambda m: substitutions[m.group(0)], content)


@lru_cache(maxsize=16)
def _get_substitution_pattern(separator: str) -> re.Pattern[str]:
    """Build and cache substitution pattern for a given separator."""
    escaped_separator = re.escape(separator)
    return re.compile(
        r"(?P<pref>[\"'])?"
        r"(\$(?:(?P<escaped>(\$|\d+))|"
        r"{(?P<braced>.*?)(?:" + escaped_separator + r"(?P<braced_default>.*?))?}|"
        r"(?P<named>[\w\-\.]+)(?:" + escaped_separator + r"(?P<named_default>.*))?))"
        r"(?P<post>[\"'])?",
        re.MULTILINE | re.UNICODE | re.IGNORECASE | re.VERBOSE,
    )


def _extract_variable_and_default(groups: dict[str, str | None]) -> tuple[str | None, str | None]:
    """Extract substitution variable and default from regex groups."""
    named = groups.get("named")
    if named:
        return named, groups.get("named_default")

    braced = groups.get("braced")
    if braced:
        return braced, groups.get("braced_default")

    return None, None


def _build_search_token(variable: str, default: str | None, is_braced: bool, separator: str) -> str:
    """Rebuild matched token text for replacement lookup."""
    search = "${" if is_braced else "$"
    search += variable
    if default is not None:
        search += separator + default
    if is_braced:
        search += "}"
    return search


def _collect_substitutions(content: str, env: EnvDict, separator: str) -> SubstitutionScanResult:
    """Scan TOML content for env substitutions and escaped tokens."""
    not_found_variables: set[str] = set()
    substitutions: dict[str, str] = {}
    segments: list[SubstitutionSegment] = []

    pattern = _get_substitution_pattern(separator)
    for entry in pattern.finditer(content):
        groups: dict[str, str | None] = entry.groupdict()

        escaped = groups.get("escaped")
        if escaped:
            start, end = entry.span()
            pref = groups.get("pref") or ""
            post = groups.get("post") or ""
            segments.append((start, end, f"{pref}{escaped}{post}"))
            continue

        variable, default = _extract_variable_and_default(groups)
        if variable is None:
            continue

        replace: str | None = None
        if variable in env:
            replace = str(env[variable])
        elif default is not None:
            replace = default
        else:
            not_found_variables.add(variable)

        if replace is None:
            continue

        search = _build_search_token(variable, default, bool(groups.get("braced")), separator)
        substitutions[search] = replace

    return substitutions, segments, not_found_variables


def _apply_escape_segments(content: str, segments: list[SubstitutionSegment]) -> str:
    """Apply escaped token replacements to content."""
    if not segments:
        return content

    result_parts: list[str] = []
    last_end = 0
    for start, end, replacement in segments:
        result_parts.append(content[last_end:start])
        result_parts.append(replacement)
        last_end = end
    result_parts.append(content[last_end:])
    return "".join(result_parts)


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
    substitutions, segments, not_found_variables = _collect_substitutions(content, env, separator)

    if strict and not_found_variables:
        raise EnvironmentVariableError.missing_variables(list(not_found_variables))

    # Apply escape replacements efficiently using segments
    content = _apply_escape_segments(content, segments)

    # Apply variable substitutions using batch regex replacement for better performance
    content = _apply_substitutions_batch(content, substitutions)

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
