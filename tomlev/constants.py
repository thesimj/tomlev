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

__all__ = [
    "TOMLEV_STRICT_DISABLE",
    "TOMLEV_TOML_FILE",
    "TOMLEV_ENV_FILE",
    "DEFAULT_TOML_FILE",
    "DEFAULT_ENV_FILE",
    "DEFAULT_SEPARATOR",
    "BOOL_TRUE_VALUES",
    "INCLUDE_KEY",
    "VERSION",
]

# Environment variable name to disable strict mode globally
TOMLEV_STRICT_DISABLE: str = "TOMLEV_STRICT_DISABLE"

# Environment variable names for default file paths
TOMLEV_TOML_FILE: str = "TOMLEV_TOML_FILE"
TOMLEV_ENV_FILE: str = "TOMLEV_ENV_FILE"

# Default file names
DEFAULT_TOML_FILE: str = "env.toml"
DEFAULT_ENV_FILE: str = ".env"

# Default separator for variable substitution
DEFAULT_SEPARATOR: str = "|-"

# Boolean true values for conversion
BOOL_TRUE_VALUES: set[str] = {"true", "1", "yes", "y", "on", "t"}

# Include directive key name
INCLUDE_KEY: str = "__include"

# Package version
VERSION: str = "1.0.4"
