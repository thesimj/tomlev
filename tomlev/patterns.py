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

import re

__all__ = [
    "RE_COMMENTS",
    "RE_DOT_ENV",
    "RE_PATTERN",
]

# Pattern to remove comments
RE_COMMENTS = re.compile(r"(^#.*\n)", re.MULTILINE | re.UNICODE | re.IGNORECASE)

# Pattern to read .env file
RE_DOT_ENV = re.compile(
    r"^(?!\d+)(?P<name>[\w\-\.]+)\=[\"\']?(?P<value>(.*?))[\"\']?$",
    re.MULTILINE | re.UNICODE | re.IGNORECASE,
)

# Pattern to extract environment variables
RE_PATTERN = re.compile(
    r"(?P<pref>[\"\'])?"
    r"(\$(?:(?P<escaped>(\$|\d+))|"
    r"{(?P<braced>(.*?))(\|-(?P<braced_default>.*?))?}|"
    r"(?P<named>[\w\-\.]+)(\|(?P<named_default>.*))?))"
    r"(?P<post>[\"\'])?",
    re.MULTILINE | re.UNICODE | re.IGNORECASE | re.VERBOSE,
)
