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

from typing import Any, TypeAlias, get_args, get_origin, get_type_hints

# Type aliases for clarity
PropertyDict: TypeAlias = dict[str, Any]
ConfigError: TypeAlias = tuple[str, str]  # (attribute, error_message)

__BOOL_VALUES__: set[str] = {"true", "1", "yes", "y", "on", "t"}


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
        # Handle None/missing values with defaults
        if value is None:
            return self._get_default_value(kind)

        # Use structural pattern matching for type conversion
        match kind:
            case t if t is bool:  # Check bool first before str since bool is subclass of int
                return self._convert_bool(value)
            case t if t is str:
                return str(value)
            case t if t is int:
                return int(value)
            case t if t is float:
                return float(value)
            case t if isinstance(t, type) and issubclass(t, BaseConfigModel):
                return t(**value) if isinstance(value, dict) else t()
            case _:
                # Handle generic types (list, dict, etc.)
                return self._convert_generic_type(attr, kind, value)

    def _convert_bool(self, value: Any) -> bool:
        """Convert value to boolean using Python 3.11 best practices."""
        match value:
            case bool():
                return value
            case str() if value.lower() in __BOOL_VALUES__:
                return True
            case str():
                return False
            case _:
                return bool(value)

    def _get_default_value(self, kind: type) -> Any:
        """Get default value for a type."""
        match kind:
            case t if t is str:
                return ""
            case t if t is int:
                return 0
            case t if t is float:
                return 0.0
            case t if t is bool:
                return False
            case t if get_origin(t) is list or t is list:
                return []
            case t if get_origin(t) is dict or t is dict:
                return {}
            case _:
                return None

    def _convert_generic_type(self, attr: str, kind: type, value: Any) -> Any:
        """Handle conversion of generic types like list[str], dict[str, int], etc."""
        origin = get_origin(kind)
        args = get_args(kind)

        match origin:
            case t if t is list or kind is list:
                return self._convert_list(args, value)
            case t if t is dict or kind is dict:
                return self._convert_dict(args, value)
            case t if t is Any:
                return value  # Keep as-is for Any
            case _:
                return value

    def _convert_list(self, args: tuple[type, ...], value: Any) -> list[Any]:
        """Convert list values with proper type conversion."""
        if not isinstance(value, list):
            raise TypeError(f"Expected list, got {type(value).__name__}")

        if not args:
            # Plain list (no type parameters) - convert all items to strings (original behavior)
            return [str(item) for item in value]

        item_type = args[0]
        converted_list: list[Any] = []

        for item in value:
            match item_type:
                case t if t is str:
                    converted_list.append(str(item))
                case t if t is int:
                    converted_list.append(int(item))
                case t if t is float:
                    converted_list.append(float(item))
                case t if t is bool:
                    converted_list.append(self._convert_bool(item))
                case t if get_origin(t) is dict:
                    # Handle list[dict[...]] types
                    converted_list.append(self._convert_dict(get_args(t), item))
                case t if str(t) == "typing.Any":
                    converted_list.append(item)
                case _:
                    converted_list.append(item)

        return converted_list

    def _convert_dict(self, args: tuple[type, ...], value: Any) -> dict[str, Any]:
        """Convert dict values with proper type conversion."""
        if not isinstance(value, dict):
            raise TypeError(f"Expected dict, got {type(value).__name__}")

        if not args or len(args) < 2:
            return dict(value)

        _, value_type = args[0], args[1]
        converted_dict: dict[str, Any] = {}

        for k, v in value.items():
            # Convert key (usually string)
            key_str = str(k)

            # Convert value based on type
            match value_type:
                case t if t is str:
                    converted_dict[key_str] = str(v)
                case t if t is int:
                    converted_dict[key_str] = int(v)
                case t if t is float:
                    converted_dict[key_str] = float(v)
                case t if t is bool:
                    converted_dict[key_str] = self._convert_bool(v)
                case t if str(t) == "typing.Any":
                    converted_dict[key_str] = v
                case _:
                    converted_dict[key_str] = v

        return converted_dict
