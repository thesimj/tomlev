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

import copy
import types
from enum import Enum
from typing import Any, TypeAlias, Union, get_args, get_origin, get_type_hints

from .converters import (
    convert_bool,
    convert_enum,
    convert_generic_type,
    convert_literal,
    convert_union,
    get_default_value,
)
from .errors import ConfigValidationError

# Type aliases for clarity
PropertyDict: TypeAlias = dict[str, Any]

__all__ = ["BaseConfigModel", "ConfigValidationError"]


class BaseConfigModel:
    """Base class for type-safe configuration models with automatic type conversion.

    BaseConfigModel provides the foundation for creating strongly-typed configuration
    classes that automatically validate and convert data types. It supports all basic
    Python types, collections, and nested configuration models.

    Supported Types:
        - Basic types: str, int, float, bool
        - Collections: list[T], dict[str, T] where T is any supported type
        - Complex collections: list[dict[str, Any]] for lists of dictionaries
        - Nested models: Other BaseConfigModel subclasses
        - Generic types: typing.Any for flexible values

    Example:
        ```python
        class DatabaseConfig(BaseConfigModel):
            host: str
            port: int
            enabled: bool
            tags: list[str]
            metadata: dict[str, Any]

        # Automatic type conversion and validation
        config = DatabaseConfig(
            host="localhost",
            port="5432",  # Automatically converted to int
            enabled="true",  # Automatically converted to bool
            tags=["prod", "db"],
            metadata={"version": "1.0", "replicas": 3}
        )

        assert config.port == 5432  # int, not str
        assert config.enabled is True  # bool, not str
        ```

    Note:
        All attribute names must match the configuration data keys exactly.
        Unknown attributes in the input data will raise an AssertionError.
    """

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        """Initialize the configuration model with automatic type conversion.

        Args:
            **kwargs: Configuration data as keyword arguments. Keys must match
                     the annotated attributes of the configuration model.

        Raises:
            AssertionError: When configuration data contains keys not defined
                          in the model's type annotations.
            ValueError: When type conversion fails for any attribute.
            TypeError: When provided values cannot be converted to expected types.
        """
        # Use get_type_hints to resolve string annotations (from __future__ import annotations)
        annotations = get_type_hints(self.__class__)
        properties: PropertyDict = {}

        # Process each annotated attribute using the old approach but with new patterns
        for attr, kind in annotations.items():
            properties[attr] = self._convert_value(attr, kind, kwargs.get(attr), kwargs)

        # Check for unknown attributes (maintain compatibility)
        for key in kwargs:
            assert key in properties, f"{key} in config file but not in config model!"  # nosec B101

        # Set all validated properties
        for key, value in properties.items():
            setattr(self, key, value)

    def _convert_value(self, attr: str, kind: type, value: Any, kwargs: dict[str, Any]) -> Any:
        """Convert a value to the specified type using pattern matching."""
        # Handle None/missing values with defaults. Prefer class defaults when set.
        if value is None:
            if hasattr(self.__class__, attr):
                default = getattr(self.__class__, attr)
                # Return a defensive copy for mutable defaults
                try:
                    return copy.deepcopy(default)
                except Exception:
                    return default
            return get_default_value(kind)

        # Use structural pattern matching for type conversion
        match kind:
            case t if isinstance(t, type) and issubclass(t, Enum):
                # Enum conversion: accept instance or coerce from name/value
                return convert_enum(t, value)
            case t if t is bool:  # Check bool first before str since bool is a subclass of int
                return convert_bool(value)
            case t if t is str:
                return str(value)
            case t if t is int:
                return int(value)
            case t if t is float:
                return float(value)
            case t if isinstance(t, type) and issubclass(t, BaseConfigModel):
                return t(**value) if isinstance(value, dict) else t()
            case _:
                # Handle Literal, Union/Optional, and generic types (list, dict, etc.)
                origin = get_origin(kind)
                if origin is not None and str(origin) == "typing.Literal":
                    return convert_literal(kind, value)
                # Union / Optional
                if origin in (Union, types.UnionType) or (origin is None and get_args(kind)):
                    return convert_union(attr, kind, value, kwargs, self._convert_value)
                return convert_generic_type(attr, kind, value, self._convert_value)

    # Convenience
    def as_dict(self) -> dict[str, Any]:
        """Return a plain dict representation of the model (recursively)."""
        result: dict[str, Any] = {}
        for attr in get_type_hints(self.__class__).keys():
            val = getattr(self, attr)
            if isinstance(val, BaseConfigModel):
                result[attr] = val.as_dict()
            elif isinstance(val, list):
                result[attr] = [v.as_dict() if isinstance(v, BaseConfigModel) else v for v in val]
            elif isinstance(val, dict):
                result[attr] = {k: (v.as_dict() if isinstance(v, BaseConfigModel) else v) for k, v in val.items()}
            else:
                result[attr] = val
        return result
