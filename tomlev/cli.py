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

import argparse
import json
from os import environ

from .constants import (
    DEFAULT_ENV_FILE,
    DEFAULT_SEPARATOR,
    DEFAULT_TOML_FILE,
    TOMLEV_ENV_FILE,
    TOMLEV_TOML_FILE,
    VERSION,
)
from .env_loader import EnvDict, read_env_file
from .errors import ConfigValidationError
from .parser import read_toml

__all__ = ["cli_validate", "cli_render", "main"]


def cli_validate(toml_file: str, env_file: str | None, strict: bool, include_environment: bool, separator: str) -> int:
    """Validate TOML parsing and env substitution without a model.

    Returns exit code 0 on success, 1 on failure. Prints a concise
    success message or a meaningful error to stderr.

    Args:
        toml_file: Path to the TOML file to validate.
        env_file: Path to the .env file, or None to skip.
        strict: Whether to operate in strict mode.
        include_environment: Whether to include system environment variables.
        separator: Separator for default values in environment variables.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    # Build env mapping
    env: EnvDict = dict(environ) if include_environment else {}
    # Read dotenv
    try:
        dotenv = read_env_file(env_file, strict)
    except Exception as e:  # noqa: BLE001  # pragma: no cover - rare environment read errors
        print(f"Error reading env file: {e}")
        return 1
    env.update(dotenv)

    # Read TOML and perform substitution
    try:
        read_toml(toml_file, env, strict, separator)
    except FileNotFoundError:
        print(f"TOML file not found: {toml_file}")
        return 1
    except ConfigValidationError as e:
        print(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"Validation error: {e}")
        return 1

    print("Validation successful.")
    return 0


def cli_render(toml_file: str, env_file: str | None, strict: bool, include_environment: bool, separator: str) -> int:
    """Render TOML configuration as JSON after environment substitution and includes.

    Returns exit code 0 on success, 1 on failure. Prints the rendered
    configuration as pretty-formatted JSON to stdout.

    Args:
        toml_file: Path to the TOML file to render.
        env_file: Path to the .env file, or None to skip.
        strict: Whether to operate in strict mode.
        include_environment: Whether to include system environment variables.
        separator: Separator for default values in environment variables.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    # Build env mapping
    env: EnvDict = dict(environ) if include_environment else {}
    # Read dotenv
    try:
        dotenv = read_env_file(env_file, strict)
    except Exception as e:  # noqa: BLE001  # pragma: no cover - rare environment read errors
        print(f"Error reading env file: {e}")
        return 1
    env.update(dotenv)

    # Read TOML and perform substitution
    try:
        config = read_toml(toml_file, env, strict, separator)
    except FileNotFoundError:
        print(f"TOML file not found: {toml_file}")
        return 1
    except ConfigValidationError as e:
        print(str(e))
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"Render error: {e}")
        return 1

    # Output as JSON
    print(json.dumps(config, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    """TomlEv CLI entry point.

    Commands:
    - validate: Validate TOML file with env substitution (schema-less).
    - render: Render TOML configuration as JSON with substitution and includes.

    Args:
        argv: Command line arguments. If None, uses sys.argv.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    # Get defaults from environment variables or fall back to constants
    default_toml = environ.get(TOMLEV_TOML_FILE, DEFAULT_TOML_FILE)
    default_env = environ.get(TOMLEV_ENV_FILE, DEFAULT_ENV_FILE)

    parser = argparse.ArgumentParser(prog="tomlev", description="TomlEv CLI")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate TOML with env substitution")
    p_validate.add_argument("--toml", default=default_toml, help="Path to TOML file")
    p_validate.add_argument("--env-file", default=default_env, help="Path to .env file (use --no-env-file to disable)")
    p_validate.add_argument("--no-env-file", action="store_true", help="Do not read .env file")
    p_validate.add_argument(
        "--strict", dest="strict", action="store_true", default=True, help="Enable strict mode (default)"
    )
    p_validate.add_argument("--no-strict", dest="strict", action="store_false", help="Disable strict mode")
    p_validate.add_argument("--no-environ", action="store_true", help="Do not include system environment variables")
    p_validate.add_argument("--separator", default=DEFAULT_SEPARATOR, help="Default separator for ${VAR|-default}")

    p_render = sub.add_parser("render", help="Render TOML configuration as JSON")
    p_render.add_argument("--toml", default=default_toml, help="Path to TOML file")
    p_render.add_argument("--env-file", default=default_env, help="Path to .env file (use --no-env-file to disable)")
    p_render.add_argument("--no-env-file", action="store_true", help="Do not read .env file")
    p_render.add_argument(
        "--strict", dest="strict", action="store_true", default=True, help="Enable strict mode (default)"
    )
    p_render.add_argument("--no-strict", dest="strict", action="store_false", help="Disable strict mode")
    p_render.add_argument("--no-environ", action="store_true", help="Do not include system environment variables")
    p_render.add_argument("--separator", default=DEFAULT_SEPARATOR, help="Default separator for ${VAR|-default}")

    args = parser.parse_args(argv)

    if args.command == "validate":
        env_file = None if args.no_env_file else args.env_file
        include_environment = not args.no_environ
        return cli_validate(args.toml, env_file, args.strict, include_environment, args.separator)
    elif args.command == "render":
        env_file = None if args.no_env_file else args.env_file
        include_environment = not args.no_environ
        return cli_render(args.toml, env_file, args.strict, include_environment, args.separator)

    parser.print_help()  # pragma: no cover - subparsers require a command
    return 1  # pragma: no cover - unreachable with required=True
