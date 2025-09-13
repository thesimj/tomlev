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
from typing import Any

from .constants import INCLUDE_KEY
from .env_loader import EnvDict
from .errors import IncludeError

__all__ = ["deep_merge", "expand_includes_dict"]


def deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge src into dst (dicts merge, scalars overwrite).

    Args:
        dst: Destination dictionary to merge into.
        src: Source dictionary to merge from.

    Returns:
        The merged destination dictionary.
    """
    for k, v in src.items():
        if k == INCLUDE_KEY:
            # never propagate include directive from included content
            continue
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def expand_includes_dict(
    node: dict[str, Any],
    base_dir: Path,
    env: EnvDict,
    strict: bool,
    separator: str,
    *,
    seen: set[Path],
    cache: dict[Path, dict[str, Any]],
    substitute_and_parse_func: Any,  # Function to substitute and parse TOML content
) -> None:
    """Recursively expand __include directives within a parsed TOML dict.

    Args:
        node: The dictionary node to process for includes.
        base_dir: Base directory for resolving relative include paths.
        env: Environment variables dictionary for substitution.
        strict: Whether to operate in strict mode for error handling.
        separator: Separator string for default values in environment variables.
        seen: Set of already seen paths to detect cycles.
        cache: Cache of already processed include files.
        substitute_and_parse_func: Function to substitute variables and parse TOML.

    Raises:
        IncludeError: When include validation fails or cycles are detected.
        FileNotFoundError: In strict mode, when included files are not found.
    """
    # Normalize and process includes at current node
    if INCLUDE_KEY in node:
        raw = node.get(INCLUDE_KEY)
        includes: list[str]
        if isinstance(raw, str):
            includes = [raw]
        elif isinstance(raw, list) and all(isinstance(x, str) for x in raw):
            includes = list(raw)
        else:
            if strict:
                raise IncludeError.invalid_type()
            includes = []

        for rel in includes:
            include_path = (base_dir / rel).resolve()
            if include_path in seen:
                if strict:
                    raise IncludeError.cycle_detected(str(include_path))
                continue
            if not include_path.is_file():
                if strict:
                    raise FileNotFoundError(f"Included TOML not found: {include_path}")
                continue

            if include_path in cache:
                sub_dict = cache[include_path]
            else:
                with io.open(include_path, mode="rt", encoding="utf8") as fp:
                    sub_content = fp.read()
                sub_dict = substitute_and_parse_func(sub_content, env, strict, separator)
                # Recurse into the included dict for its own includes, carry seen
                expand_includes_dict(
                    sub_dict,
                    include_path.parent,
                    env,
                    strict,
                    separator,
                    seen=seen | {include_path},
                    cache=cache,
                    substitute_and_parse_func=substitute_and_parse_func,
                )
                cache[include_path] = sub_dict

            deep_merge(node, sub_dict)

        # Remove directive after processing
        node.pop(INCLUDE_KEY, None)

    # Recurse into children
    for k, v in list(node.items()):
        if isinstance(v, dict):
            expand_includes_dict(
                v,
                base_dir,
                env,
                strict,
                separator,
                seen=seen,
                cache=cache,
                substitute_and_parse_func=substitute_and_parse_func,
            )
