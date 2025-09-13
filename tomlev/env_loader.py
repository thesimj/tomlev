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
from os.path import expandvars
from pathlib import Path
from typing import Any, TypeAlias

from .errors import EnvironmentVariableError

__all__ = ["EnvDict", "read_env_file"]

# Type aliases for clarity
EnvDict: TypeAlias = dict[str, Any]


def read_env_file(file_path: str | None, strict: bool = True) -> EnvDict:
    """Read and parse environment variables from a .env file.

    Supports:
    - Optional "export " prefix
    - Quoted values (single or double)
    - Escapes in double-quoted values (\n, \t, \", \\)
    - Inline comments after unquoted values
    - Environment expansion (via os.path.expandvars)

    Args:
        file_path: Path to the .env file to read. If None or file doesn't exist, returns empty dict.
        strict: Whether to enforce strict mode validation for duplicate variables.

    Returns:
        Dictionary containing parsed environment variables.

    Raises:
        EnvironmentVariableError: In strict mode, when duplicate variables are found.
    """
    config: EnvDict = {}
    defined: set[str] = set()

    if not file_path or not Path(file_path).is_file():
        return config

    def _unquote(val: str) -> str:
        """Strip matching quotes and unescape simple sequences for double-quoted values.

        Single-quoted values are treated literally; double-quoted values support
        a minimal set of escape sequences (\\n, \\t, \\" and \\\\).
        """
        val = val.strip()
        if len(val) >= 2 and ((val[0] == val[-1] == '"') or (val[0] == val[-1] == "'")):
            inner = val[1:-1]
            if val[0] == '"':
                # Process simple escape sequences
                inner = inner.replace(r"\\", "\\").replace(r"\n", "\n").replace(r"\t", "\t").replace(r"\"", '"')
            return inner
        return val

    with io.open(file_path, mode="rt", encoding="utf8") as fp:
        for raw in fp:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            # Expand environment variables first
            line = expandvars(line)

            # Allow optional export prefix
            if line.startswith("export "):
                line = line[len("export ") :].lstrip()

            if "=" not in line:
                continue

            name, val = line.split("=", 1)
            name = name.strip()
            # Basic validation: start with non-digit, allow word, dash, dot, underscore
            if not name or name[0].isdigit():
                continue

            # Handle inline comments for unquoted values
            v = val.lstrip()
            if v.startswith('"') or v.startswith("'"):
                value = _unquote(v)
            else:
                # Cut off at first unescaped '#'. Support escaping with '\#'.
                cut: list[str] = []
                escaped = False
                for ch in v:
                    if escaped:
                        cut.append(ch)
                        escaped = False
                        continue
                    if ch == "\\":
                        escaped = True
                        continue
                    if ch == "#":
                        break
                    cut.append(ch)
                value = "".join(cut).strip()

            if name in config:
                defined.add(name)
            config[name] = value

    if strict and defined:
        raise EnvironmentVariableError.duplicate_variables(list(defined))

    return config
