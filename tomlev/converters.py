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

from enum import Enum
from typing import Any, get_args, get_origin

from .constants import BOOL_TRUE_VALUES

__all__ = [
    "convert_bool",
    "convert_enum",
    "convert_literal",
    "convert_union",
    "convert_list",
    "convert_dict",
    "convert_set",
    "convert_tuple",
    "convert_generic_type",
    "get_default_value",
]


def convert_bool(value: Any) -> bool:
    """Convert value to boolean using Python 3.11 best practices.

    Args:
        value: Value to convert to boolean.

    Returns:
        Boolean representation of the value.
    """
    match value:
        case bool():
            return value
        case str() if value.lower() in BOOL_TRUE_VALUES:
            return True
        case str():
            return False
        case _:
            return bool(value)


def convert_enum(enum_type: type[Enum], value: Any) -> Enum:
    """Convert a value to an Enum member.

    Accepts:
    - Enum instance (returned as-is)
    - String value matching member name (case-insensitive) or member value
    - Other values that equal a member's value

    Args:
        enum_type: The enum class to convert to.
        value: Value to convert to enum member.

    Returns:
        Enum member matching the value.

    Raises:
        ValueError: When value cannot be converted to enum member.
    """
    if isinstance(value, enum_type):
        return value

    # Attempt by name (case-insensitive for convenience)
    if isinstance(value, str):
        name = value
        # Try exact name
        if name in enum_type.__members__:
            return enum_type.__members__[name]
        # Try upper case name
        upper = name.upper()
        if upper in enum_type.__members__:
            return enum_type.__members__[upper]

    # Attempt by value equality
    for member in enum_type:
        if isinstance(value, str):
            if str(member.value) == value:
                return member
        else:
            if member.value == value:
                return member

    raise ValueError(f"Invalid value {value!r} for enum {enum_type.__name__}")


def convert_literal(literal_type: Any, value: Any) -> Any:
    """Validate/convert a value against a typing.Literal set of allowed values.

    Args:
        literal_type: The Literal type with allowed values.
        value: Value to validate against literal type.

    Returns:
        Converted value if valid.

    Raises:
        ValueError: When value is not in allowed literal values.
    """
    allowed = get_args(literal_type)
    if not allowed:
        return value

    # Infer common type from the first allowed value
    sample = allowed[0]
    conv: Any
    try:
        if isinstance(sample, bool):
            conv = convert_bool(value)
        elif isinstance(sample, int) and not isinstance(sample, bool):
            conv = int(value)
        elif isinstance(sample, float):
            conv = float(value)
        else:
            conv = str(value)
    except (TypeError, ValueError):
        # If conversion fails, keep original for membership check
        conv = value

    if conv in allowed:
        return conv

    # Also consider raw string equality with allowed values
    if isinstance(value, str) and any(str(a) == value for a in allowed):
        return value

    raise ValueError(f"Value {value!r} not in allowed Literal{allowed}")


def convert_union(attr: str, union_type: Any, value: Any, kwargs: dict[str, Any], convert_value_func: Any) -> Any:
    """Convert value according to a Union (including Optional).

    Args:
        attr: Attribute name for error context.
        union_type: The Union type annotation.
        value: Value to convert.
        kwargs: Additional keyword arguments for context.
        convert_value_func: Function to convert values recursively.

    Returns:
        Converted value according to one of the union types.

    Raises:
        Exception: When value cannot be converted to any of the union types.
    """
    args = get_args(union_type)
    if not args:
        return value

    # Optional support
    if value is None and type(None) in args:
        return None

    last_exc: Exception | None = None
    # Try each type in order, skipping NoneType
    for t in args:
        if t is type(None):
            continue
        try:
            return convert_value_func(attr, t, value, kwargs)
        except Exception as e:  # noqa: BLE001 - intentionally catching conversion attempts
            last_exc = e
            continue

    if last_exc:
        raise last_exc
    return value


def convert_list(args: tuple[type, ...], value: Any, convert_value_func: Any) -> list[Any]:
    """Convert list values with proper type conversion.

    Args:
        args: Type arguments for the list (e.g., for list[str], args would be (str,)).
        value: Value to convert to list.
        convert_value_func: Function to convert values recursively.

    Returns:
        List with properly converted items.

    Raises:
        TypeError: When value is not a list.
    """
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
                converted_list.append(convert_bool(item))
            case t if t is not Any and hasattr(t, "__annotations__"):  # BaseConfigModel check without circular import
                converted_list.append(t(**item) if isinstance(item, dict) else t())
            case t if get_origin(t) is dict:
                # Handle list[dict[...]] types
                converted_list.append(convert_dict(get_args(t), item, convert_value_func))
            case t if t is Any:
                converted_list.append(item)
            case _:
                converted_list.append(item)

    return converted_list


def convert_dict(args: tuple[type, ...], value: Any, convert_value_func: Any) -> dict[str, Any]:
    """Convert dict values with proper type conversion.

    Args:
        args: Type arguments for the dict (e.g., for dict[str, int], args would be (str, int)).
        value: Value to convert to dict.
        convert_value_func: Function to convert values recursively.

    Returns:
        Dictionary with properly converted values.

    Raises:
        TypeError: When value is not a dict.
    """
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
                converted_dict[key_str] = convert_bool(v)
            case t if t is Any:
                converted_dict[key_str] = v
            case t if t is not Any and hasattr(t, "__annotations__"):  # BaseConfigModel check without circular import
                converted_dict[key_str] = t(**v) if isinstance(v, dict) else t()
            case _:
                converted_dict[key_str] = v

    return converted_dict


def convert_set(args: tuple[type, ...], value: Any, convert_value_func: Any) -> set[Any]:
    """Convert list values to set with proper type conversion.

    Args:
        args: Type arguments for the set (e.g., for set[str], args would be (str,)).
        value: Value to convert to set.
        convert_value_func: Function to convert values recursively.

    Returns:
        Set with properly converted items.

    Raises:
        TypeError: When value is not a list.
    """
    if not isinstance(value, list):
        raise TypeError(f"Expected list for set conversion, got {type(value).__name__}")

    if not args:
        # Plain set (no type parameters) - convert all items to strings
        return {str(item) for item in value}

    item_type = args[0]
    converted_set: set[Any] = set()

    for item in value:
        match item_type:
            case t if t is str:
                converted_set.add(str(item))
            case t if t is int:
                converted_set.add(int(item))
            case t if t is float:
                converted_set.add(float(item))
            case t if t is bool:
                converted_set.add(convert_bool(item))
            case t if t is Any:
                converted_set.add(item)
            case _:
                converted_set.add(item)

    return converted_set


def convert_tuple(args: tuple[type, ...], value: Any, convert_value_func: Any) -> tuple[Any, ...]:
    """Convert list values to tuple with proper type conversion.

    Args:
        args: Type arguments for the tuple (e.g., for tuple[str, int, float], args would be (str, int, float)).
        value: Value to convert to tuple.
        convert_value_func: Function to convert values recursively.

    Returns:
        Tuple with properly converted items.

    Raises:
        TypeError: When value is not a list.
    """
    if not isinstance(value, list):
        raise TypeError(f"Expected list for tuple conversion, got {type(value).__name__}")

    converted_list: list[Any] = []

    if not args:
        # Plain tuple (no type parameters) - convert all items to strings
        return tuple(str(item) for item in value)

    # For typed tuples, convert each element according to its position type
    for i, item in enumerate(value):
        if i < len(args):
            item_type = args[i]
            match item_type:
                case t if t is str:
                    converted_list.append(str(item))
                case t if t is int:
                    converted_list.append(int(item))
                case t if t is float:
                    converted_list.append(float(item))
                case t if t is bool:
                    converted_list.append(convert_bool(item))
                case t if t is Any:
                    converted_list.append(item)
                case _:
                    converted_list.append(item)
        else:
            # If more items than type hints, keep original values
            converted_list.append(item)

    return tuple(converted_list)


def convert_generic_type(attr: str, kind: type, value: Any, convert_value_func: Any) -> Any:
    """Handle conversion of generic types like list[str], dict[str, int], etc.

    Args:
        attr: Attribute name for error context.
        kind: The generic type to convert to.
        value: Value to convert.
        convert_value_func: Function to convert values recursively.

    Returns:
        Converted value according to the generic type.
    """
    origin = get_origin(kind)
    args = get_args(kind)

    match origin:
        case t if t is list or kind is list:
            return convert_list(args, value, convert_value_func)
        case t if t is dict or kind is dict:
            return convert_dict(args, value, convert_value_func)
        case t if t is set or kind is set:
            return convert_set(args, value, convert_value_func)
        case t if t is tuple or kind is tuple:
            return convert_tuple(args, value, convert_value_func)
        case _:
            return value


def get_default_value(kind: type) -> Any:
    """Get default value for a type.

    Args:
        kind: The type to get default value for.

    Returns:
        Default value for the type.
    """
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
        case t if get_origin(t) is set or t is set:
            return set()
        case t if get_origin(t) is tuple or t is tuple:
            return ()
        case _:
            return None
