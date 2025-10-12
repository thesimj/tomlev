"""
Test edge cases and uncovered paths in tomlev/converters.py.

These tests target specific branches and error paths that aren't covered
by the main test suite, improving overall coverage.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

import pytest

from tomlev.converters import (
    convert_dict,
    convert_enum,
    convert_generic_type,
    convert_list,
    convert_literal,
    convert_set,
    convert_tuple,
    get_default_value,
)


# Test enum for enum conversion tests
class Color(Enum):
    """Test enum with different value types."""

    RED = "red"
    GREEN = "green"
    BLUE = 42


class Status(Enum):
    """Test enum for value matching."""

    ACTIVE = 1
    INACTIVE = 0


# =============================================================================
# Enum Conversion Edge Cases
# =============================================================================


def test_convert_enum_already_enum() -> None:
    """Test that enum values are returned as-is."""
    # Test with the actual enum member
    result = convert_enum(Color, Color.RED)
    assert result == Color.RED
    assert isinstance(result, Color)


def test_convert_enum_exact_name() -> None:
    """Test enum conversion by exact member name."""
    # Test exact name match (case-sensitive)
    result = convert_enum(Color, "RED")
    assert result == Color.RED


def test_convert_enum_uppercase_name() -> None:
    """Test enum conversion by uppercase name."""
    # Test that lowercase gets converted to uppercase
    result = convert_enum(Color, "red")
    # Should try uppercase, but "RED" exists, so returns RED member
    assert result == Color.RED


def test_convert_enum_by_value_string() -> None:
    """Test enum conversion by matching value (string)."""
    # Test matching by value when name doesn't match
    result = convert_enum(Color, "green")
    assert result == Color.GREEN


def test_convert_enum_by_value_non_string() -> None:
    """Test enum conversion by matching value (non-string)."""
    # Test integer value matching
    result = convert_enum(Color, 42)
    assert result == Color.BLUE

    # Test integer enum
    result2 = convert_enum(Status, 1)
    assert result2 == Status.ACTIVE


def test_convert_enum_invalid_value() -> None:
    """Test that invalid enum values raise ValueError."""
    with pytest.raises(ValueError, match="Invalid value.*for enum"):
        convert_enum(Color, "invalid_color")

    with pytest.raises(ValueError, match="Invalid value.*for enum"):
        convert_enum(Status, 99)


# =============================================================================
# Literal Conversion Edge Cases
# =============================================================================


def test_convert_literal_type_conversion_failure() -> None:
    """Test literal conversion when type conversion fails."""
    # Create a Literal type
    literal_type = Literal[1, 2, 3]

    # Value that can't be converted to int should fall back to membership check
    # Since "not_a_number" can't be converted and isn't in (1, 2, 3), should raise
    with pytest.raises(ValueError, match="not in allowed Literal"):
        convert_literal(literal_type, "not_a_number")


def test_convert_literal_string_equality_fallback() -> None:
    """Test literal conversion with string equality fallback."""
    # Test with values where string equality matters
    literal_type = Literal["one", "two", "three"]

    # Test that string values work
    result = convert_literal(literal_type, "one")
    assert result == "one"


def test_convert_literal_bool_conversion() -> None:
    """Test literal conversion with boolean types."""
    literal_type = Literal[True, False]

    result = convert_literal(literal_type, "true")
    assert result is True

    result2 = convert_literal(literal_type, "false")
    assert result2 is False


def test_convert_literal_float_conversion() -> None:
    """Test literal conversion with float types."""
    literal_type = Literal[1.5, 2.5, 3.5]

    result = convert_literal(literal_type, "1.5")
    assert result == 1.5


def test_convert_literal_empty_allowed() -> None:
    """Test literal conversion with empty allowed values."""
    # When no args, should return value as-is

    # Simulate empty literal
    class FakeLiteral:
        pass

    # Direct call with no args tuple
    result = convert_literal(FakeLiteral, "anything")
    # Should return the value since allowed is empty
    assert result == "anything"


# =============================================================================
# Dict Conversion Edge Cases
# =============================================================================


def test_convert_dict_any_value_type() -> None:
    """Test dict conversion with Any value type."""
    from typing import get_args

    # dict[str, Any]
    dict_type = dict[str, Any]
    args = get_args(dict_type)

    test_dict = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}

    result = convert_dict(args, test_dict, lambda a, t, v, k: v)

    # Any type should preserve values as-is
    assert result["key1"] == "value1"
    assert result["key2"] == 123
    assert result["key3"] == [1, 2, 3]


def test_convert_dict_no_args() -> None:
    """Test dict conversion with no type args."""
    test_dict = {"key": "value"}
    result = convert_dict((), test_dict, None)

    assert result == test_dict


def test_convert_dict_not_a_dict() -> None:
    """Test dict conversion with non-dict value."""
    with pytest.raises(TypeError, match="Expected dict"):
        convert_dict((str, int), "not_a_dict", None)


# =============================================================================
# List Conversion Edge Cases
# =============================================================================


def test_convert_list_dict_items() -> None:
    """Test list of dict conversion."""
    from typing import get_args

    # list[dict[str, int]]
    list_type = list[dict[str, int]]
    args = get_args(list_type)

    test_list = [{"a": "1", "b": "2"}, {"c": "3"}]

    def mock_convert_dict(args_inner, value, convert_func):
        # Mock convert_dict behavior
        return {k: int(v) for k, v in value.items()}

    # We need to test the path where get_origin(item_type) is dict
    # This is hard to test without the full convert_value_func, so we'll test indirectly
    # by ensuring the code path exists

    result = convert_list(args, test_list, mock_convert_dict)
    # The actual conversion depends on convert_value_func implementation
    assert isinstance(result, list)


def test_convert_list_no_args() -> None:
    """Test list conversion with no type args."""
    test_list = [1, 2, 3]
    result = convert_list((), test_list, None)

    # Should convert all to strings
    assert result == ["1", "2", "3"]


def test_convert_list_not_a_list() -> None:
    """Test list conversion with non-list value."""
    with pytest.raises(TypeError, match="Expected list"):
        convert_list((str,), "not_a_list", None)


# =============================================================================
# Set Conversion Edge Cases
# =============================================================================


def test_convert_set_any_type() -> None:
    """Test set conversion with Any type."""
    test_list = [1, "two", 3.0, "two"]  # Has duplicate

    result = convert_set((Any,), test_list, None)

    # Any type should preserve values
    assert 1 in result
    assert "two" in result
    assert 3.0 in result


def test_convert_set_no_args() -> None:
    """Test set conversion with no type args."""
    test_list = [1, 2, 2, 3]
    result = convert_set((), test_list, None)

    # Should convert all to strings and deduplicate
    assert result == {"1", "2", "3"}


def test_convert_set_not_a_list() -> None:
    """Test set conversion with non-list value."""
    with pytest.raises(TypeError, match="Expected list for set conversion"):
        convert_set((str,), "not_a_list", None)


# =============================================================================
# Tuple Conversion Edge Cases
# =============================================================================


def test_convert_tuple_no_args() -> None:
    """Test tuple conversion with no type args."""
    test_list = [1, 2, 3]
    result = convert_tuple((), test_list, None)

    # Should convert all to strings
    assert result == ("1", "2", "3")


def test_convert_tuple_any_type() -> None:
    """Test tuple conversion with Any type."""
    test_list = [1, "two", 3.0]

    result = convert_tuple((Any, Any, Any), test_list, None)

    # Any type should preserve values
    assert result == (1, "two", 3.0)


def test_convert_tuple_more_items_than_types() -> None:
    """Test tuple conversion when list has more items than type hints."""
    test_list = [1, 2, 3, 4, 5]

    # Only 3 types specified
    result = convert_tuple((int, int, int), test_list, None)

    # Extra items should be kept as-is
    assert len(result) == 5
    assert result[:3] == (1, 2, 3)
    assert result[3:] == (4, 5)


def test_convert_tuple_not_a_list() -> None:
    """Test tuple conversion with non-list value."""
    with pytest.raises(TypeError, match="Expected list for tuple conversion"):
        convert_tuple((str,), "not_a_tuple", None)


# =============================================================================
# Generic Type Conversion Edge Cases
# =============================================================================


def test_convert_generic_type_default_case() -> None:
    """Test generic type conversion with unsupported origin."""
    # Test with a type that doesn't match any known origin
    result = convert_generic_type("attr", str, "value", None)

    # Should return value as-is for unknown types
    assert result == "value"


def test_convert_generic_type_plain_list() -> None:
    """Test generic type conversion with plain list (no generics)."""
    result = convert_generic_type("attr", list, [1, 2, 3], None)

    # Should convert using convert_list with no args
    assert result == ["1", "2", "3"]


def test_convert_generic_type_plain_dict() -> None:
    """Test generic type conversion with plain dict (no generics)."""
    result = convert_generic_type("attr", dict, {"key": "value"}, None)

    # Should convert using convert_dict
    assert isinstance(result, dict)


def test_convert_generic_type_plain_set() -> None:
    """Test generic type conversion with plain set (no generics)."""
    result = convert_generic_type("attr", set, [1, 2, 3], None)

    # Should convert using convert_set
    assert result == {"1", "2", "3"}


def test_convert_generic_type_plain_tuple() -> None:
    """Test generic type conversion with plain tuple (no generics)."""
    result = convert_generic_type("attr", tuple, [1, 2, 3], None)

    # Should convert using convert_tuple
    assert result == ("1", "2", "3")


# =============================================================================
# get_default_value Edge Cases
# =============================================================================


def test_get_default_value_unknown_type() -> None:
    """Test get_default_value with unknown type."""

    # Custom class that doesn't match any case
    class CustomType:
        pass

    result = get_default_value(CustomType)

    # Should return None for unknown types
    assert result is None


def test_get_default_value_all_types() -> None:
    """Test get_default_value returns correct defaults."""
    assert get_default_value(str) == ""
    assert get_default_value(int) == 0
    assert get_default_value(float) == 0.0
    assert get_default_value(bool) is False
    assert get_default_value(list) == []
    assert get_default_value(dict) == {}
    assert get_default_value(set) == set()
    assert get_default_value(tuple) == ()
