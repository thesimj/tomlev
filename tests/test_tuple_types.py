"""Comprehensive tests for tuple type conversion in TomlEv."""

from __future__ import annotations

import tempfile
from typing import Any

import pytest

from tomlev import BaseConfigModel, TomlEv
from tomlev.converters import convert_tuple


class TupleTypesConfig(BaseConfigModel):
    """Configuration model with various tuple types for testing."""

    str_int_float_tuple: tuple[str, int, float]
    bool_tuple: tuple[bool, bool, bool]
    any_tuple: tuple[Any, Any, Any]
    single_tuple: tuple[str]
    mixed_tuple: tuple[str, int, float, bool, Any]
    empty_tuple: tuple[()]


class PlainTupleConfig(BaseConfigModel):
    """Configuration model with plain tuple (no type parameters)."""

    plain_tuple: tuple


class VariableLengthTupleConfig(BaseConfigModel):
    """Configuration with variable length tuples."""

    short_tuple: tuple[str, int]  # Expects 2 items
    long_tuple: tuple[str, int, float]  # Expects 3 items


class NestedTupleConfig(BaseConfigModel):
    """Configuration with nested model that has tuples."""

    coordinates: tuple[float, float, float]
    metadata: tuple[str, int]


class ConfigWithTuples(BaseConfigModel):
    """Configuration with tuples in various contexts."""

    location: tuple[float, float]
    nested: NestedTupleConfig


def test_typed_tuple_conversion():
    """Test converting list to typed tuple with correct positional types."""
    toml_content = """
    str_int_float_tuple = ["hello", "42", 3.14]
    bool_tuple = [true, false, "yes"]
    any_tuple = ["text", 123, true]
    single_tuple = ["single"]
    mixed_tuple = ["text", 42, 3.14, false, "anything"]
    empty_tuple = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(TupleTypesConfig, f.name).validate()

        # Check str_int_float_tuple
        assert config.str_int_float_tuple == ("hello", 42, 3.14)
        assert isinstance(config.str_int_float_tuple[0], str)
        assert isinstance(config.str_int_float_tuple[1], int)
        assert isinstance(config.str_int_float_tuple[2], float)

        # Check bool_tuple
        assert config.bool_tuple == (True, False, True)
        assert all(isinstance(x, bool) for x in config.bool_tuple)

        # Check any_tuple
        assert config.any_tuple == ("text", 123, True)

        # Check single_tuple
        assert config.single_tuple == ("single",)
        assert len(config.single_tuple) == 1

        # Check mixed_tuple
        assert config.mixed_tuple == ("text", 42, 3.14, False, "anything")
        assert isinstance(config.mixed_tuple[0], str)
        assert isinstance(config.mixed_tuple[1], int)
        assert isinstance(config.mixed_tuple[2], float)
        assert isinstance(config.mixed_tuple[3], bool)


def test_tuple_with_more_items_than_types():
    """Test tuple with more items than type hints."""
    toml_content = """
    short_tuple = ["first", 2, "extra1", "extra2"]
    long_tuple = ["one", 2, 3.0]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(VariableLengthTupleConfig, f.name).validate()

        # First two items should be converted according to types, rest kept as-is
        assert config.short_tuple == ("first", 2, "extra1", "extra2")
        assert isinstance(config.short_tuple[0], str)
        assert isinstance(config.short_tuple[1], int)

        assert config.long_tuple == ("one", 2, 3.0)


def test_tuple_with_fewer_items_than_types():
    """Test tuple with fewer items than type hints."""
    toml_content = """
    short_tuple = ["only_one"]
    long_tuple = ["one", 2]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(VariableLengthTupleConfig, f.name).validate()

        # Should handle gracefully with fewer items
        assert config.short_tuple == ("only_one",)
        assert config.long_tuple == ("one", 2)


def test_empty_tuple():
    """Test empty tuple handling."""
    toml_content = """
    str_int_float_tuple = ["a", 1, 1.0]
    bool_tuple = [true, false, true]
    any_tuple = [1, 2, 3]
    single_tuple = ["x"]
    mixed_tuple = ["a", 1, 1.0, true, "b"]
    empty_tuple = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(TupleTypesConfig, f.name).validate()

        assert config.empty_tuple == ()
        assert isinstance(config.empty_tuple, tuple)
        assert len(config.empty_tuple) == 0


def test_plain_tuple_without_type_params():
    """Test plain tuple without type parameters converts all to strings."""
    toml_content = """
    plain_tuple = [1, 2.5, "three", true, false]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(PlainTupleConfig, f.name).validate()

        # All items should be converted to strings
        assert config.plain_tuple == ("1", "2.5", "three", "True", "False")
        assert all(isinstance(x, str) for x in config.plain_tuple)


def test_tuple_with_env_substitution():
    """Test tuple with environment variable substitution."""
    toml_content = """
    str_int_float_tuple = ["${TEXT|-default_text}", "${NUM|-42}", "${FLOAT|-3.14}"]
    bool_tuple = ["${BOOL1|-yes}", "${BOOL2|-no}", "${BOOL3|-true}"]
    any_tuple = ["${ANY1|-value1}", "${ANY2|-123}", "${ANY3|-false}"]
    single_tuple = ["${SINGLE|-single_value}"]
    mixed_tuple = ["${STR|-text}", "${INT|-10}", "${FLOAT|-2.5}", "${BOOL|-false}", "${ANY|-any}"]
    empty_tuple = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(TupleTypesConfig, f.name).validate()

        assert config.str_int_float_tuple == ("default_text", 42, 3.14)
        assert config.bool_tuple == (True, False, True)
        assert config.single_tuple == ("single_value",)


def test_convert_tuple_error_handling():
    """Test error handling in convert_tuple function."""
    # Test with non-list input
    with pytest.raises(TypeError, match="Expected list for tuple conversion"):
        convert_tuple((str, int), "not_a_list", None)

    with pytest.raises(TypeError, match="Expected list for tuple conversion"):
        convert_tuple((int,), {"key": "value"}, None)

    with pytest.raises(TypeError, match="Expected list for tuple conversion"):
        convert_tuple((), 123, None)


def test_convert_tuple_without_args():
    """Test convert_tuple with no type arguments (plain tuple)."""
    result = convert_tuple((), [1, 2.5, "text", True, None], None)
    assert result == ("1", "2.5", "text", "True", "None")
    assert all(isinstance(x, str) for x in result)


def test_convert_tuple_with_various_types():
    """Test convert_tuple directly with different type arguments."""
    # Test with str, int, float types
    result1 = convert_tuple((str, int, float), ["hello", "42", "3.14"], None)
    assert result1 == ("hello", 42, 3.14)
    assert isinstance(result1[0], str)
    assert isinstance(result1[1], int)
    assert isinstance(result1[2], float)

    # Test with bool types
    result2 = convert_tuple((bool, bool), ["yes", 0], None)
    assert result2 == (True, False)

    # Test with Any type
    result3 = convert_tuple((Any, Any), ["text", 123], None)
    assert result3 == ("text", 123)

    # Test with unknown type (fallback case)
    class CustomType:
        pass

    result4 = convert_tuple((CustomType,), ["value"], None)
    assert result4 == ("value",)


def test_convert_tuple_position_based():
    """Test that tuple conversion is position-based, not type-uniform."""
    # Each position should use its corresponding type
    result = convert_tuple(
        (str, int, float, bool, Any),
        ["100", "200", "300", "yes", {"key": "value"}],
        None,
    )

    assert result == ("100", 200, 300.0, True, {"key": "value"})
    assert isinstance(result[0], str)  # "100" as str
    assert isinstance(result[1], int)  # 200 as int
    assert isinstance(result[2], float)  # 300.0 as float
    assert isinstance(result[3], bool)  # True from "yes"
    assert isinstance(result[4], dict)  # Kept as-is for Any


def test_nested_config_with_tuples():
    """Test nested configuration models containing tuples."""
    toml_content = """
    location = [52.5200, 13.4050]

    [nested]
    coordinates = [1.0, 2.0, 3.0]
    metadata = ["sensor_1", "42"]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(ConfigWithTuples, f.name).validate()

        assert config.location == (52.5200, 13.4050)
        assert config.nested.coordinates == (1.0, 2.0, 3.0)
        assert config.nested.metadata == ("sensor_1", 42)


def test_tuple_immutability():
    """Test that tuples are immutable after creation."""
    toml_content = """
    str_int_float_tuple = ["a", 1, 1.0]
    bool_tuple = [true, false, true]
    any_tuple = [1, 2, 3]
    single_tuple = ["x"]
    mixed_tuple = ["a", 1, 1.0, true, "b"]
    empty_tuple = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(TupleTypesConfig, f.name).validate()

        # Tuples should be immutable
        with pytest.raises(TypeError):
            config.str_int_float_tuple[0] = "changed"

        with pytest.raises(AttributeError):
            config.empty_tuple.append("item")


def test_tuple_type_coercion_edge_cases():
    """Test edge cases in type coercion for tuples."""
    toml_content = """
    # String representations of numbers
    str_int_float_tuple = ["123", "456", "789.012"]

    # Various boolean representations
    bool_tuple = [1, 0, "False"]

    # Mixed any types (using empty arrays and tables instead of null)
    any_tuple = [[], {}, "value"]

    # Single item
    single_tuple = [123]

    # Complex mixed types (removed null which is not valid TOML)
    mixed_tuple = [123, "456", "789.0", 0, "none"]

    empty_tuple = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(TupleTypesConfig, f.name).validate()

        # Check type coercions
        assert config.str_int_float_tuple == ("123", 456, 789.012)
        assert config.bool_tuple == (True, False, False)
        assert config.single_tuple == ("123",)  # int -> str
        assert config.mixed_tuple == ("123", 456, 789.0, False, "none")


def test_tuple_overflow_items():
    """Test handling of extra items beyond tuple type definition."""

    class OverflowTupleConfig(BaseConfigModel):
        fixed_tuple: tuple[str, int]  # Expects exactly 2 items

    toml_content = """
    # More items than type hints
    fixed_tuple = ["first", 2, "third", "fourth", 5]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(OverflowTupleConfig, f.name).validate()

        # Extra items beyond type hints are kept as-is
        assert config.fixed_tuple == ("first", 2, "third", "fourth", 5)
        assert len(config.fixed_tuple) == 5
        assert isinstance(config.fixed_tuple[0], str)
        assert isinstance(config.fixed_tuple[1], int)
        # Extra items kept as original types
        assert config.fixed_tuple[2] == "third"
        assert config.fixed_tuple[3] == "fourth"
        assert config.fixed_tuple[4] == 5
