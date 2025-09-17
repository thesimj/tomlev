"""Comprehensive tests for set type conversion in TomlEv."""

from __future__ import annotations

import tempfile
from typing import Any

import pytest

from tomlev import BaseConfigModel, TomlEv
from tomlev.converters import convert_set


class SetTypesConfig(BaseConfigModel):
    """Configuration model with various set types for testing."""

    str_set: set[str]
    int_set: set[int]
    float_set: set[float]
    bool_set: set[bool]
    any_set: set[Any]
    empty_set: set[str]


class PlainSetConfig(BaseConfigModel):
    """Configuration model with plain set (no type parameters)."""

    plain_set: set


class NestedSetConfig(BaseConfigModel):
    """Configuration with nested model that has sets."""

    name: str
    tags: set[str]


class ConfigWithNestedSets(BaseConfigModel):
    """Configuration with nested configs containing sets."""

    configs: list[NestedSetConfig]


def test_string_set_conversion():
    """Test converting list to set[str] with string items."""
    toml_content = """
    str_set = ["apple", "banana", "cherry", "apple"]
    int_set = []
    float_set = []
    bool_set = []
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        # Check deduplication works
        assert config.str_set == {"apple", "banana", "cherry"}
        assert len(config.str_set) == 3
        assert isinstance(config.str_set, set)


def test_int_set_conversion():
    """Test converting list to set[int] with integer items."""
    toml_content = """
    str_set = []
    int_set = [1, 2, 3, 2, "4", 5.0]
    float_set = []
    bool_set = []
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        assert config.int_set == {1, 2, 3, 4, 5}
        assert all(isinstance(x, int) for x in config.int_set)


def test_float_set_conversion():
    """Test converting list to set[float] with float items."""
    toml_content = """
    str_set = []
    int_set = []
    float_set = [1.5, 2.5, 3, "4.5", 2.5]
    bool_set = []
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        assert config.float_set == {1.5, 2.5, 3.0, 4.5}
        assert all(isinstance(x, float) for x in config.float_set)


def test_bool_set_conversion():
    """Test converting list to set[bool] with boolean items."""
    toml_content = """
    str_set = []
    int_set = []
    float_set = []
    bool_set = [true, false, "yes", "no", 1, 0, true]
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        # Should have True and False
        assert config.bool_set == {True, False}
        assert len(config.bool_set) == 2


def test_any_set_conversion():
    """Test converting list to set[Any] with mixed types."""
    toml_content = """
    str_set = []
    int_set = []
    float_set = []
    bool_set = []
    any_set = ["text", 42, 3.14, true]
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        assert config.any_set == {"text", 42, 3.14, True}
        assert isinstance(config.any_set, set)


def test_empty_set():
    """Test empty set handling."""
    toml_content = """
    str_set = []
    int_set = []
    float_set = []
    bool_set = []
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        assert config.empty_set == set()
        assert isinstance(config.empty_set, set)


def test_plain_set_without_type_params():
    """Test plain set without type parameters converts to set of strings."""
    toml_content = """
    plain_set = [1, 2, "three", 4.5, true]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(PlainSetConfig, f.name).validate()

        # All items should be converted to strings
        assert config.plain_set == {"1", "2", "three", "4.5", "True"}
        assert all(isinstance(x, str) for x in config.plain_set)


def test_set_with_env_substitution():
    """Test set with environment variable substitution."""
    toml_content = """
    str_set = ["${ITEM1|-default1}", "${ITEM2|-default2}", "${ITEM1|-default1}"]
    int_set = []
    float_set = []
    bool_set = []
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        # Should deduplicate default1
        assert config.str_set == {"default1", "default2"}


def test_convert_set_error_handling():
    """Test error handling in convert_set function."""
    # Test with non-list input
    with pytest.raises(TypeError, match="Expected list for set conversion"):
        convert_set((str,), "not_a_list", None)

    with pytest.raises(TypeError, match="Expected list for set conversion"):
        convert_set((int,), {"key": "value"}, None)

    with pytest.raises(TypeError, match="Expected list for set conversion"):
        convert_set((), 123, None)


def test_convert_set_without_args():
    """Test convert_set with no type arguments (plain set)."""
    result = convert_set((), [1, 2.5, "text", True], None)
    assert result == {"1", "2.5", "text", "True"}
    assert all(isinstance(x, str) for x in result)


def test_convert_set_with_various_types():
    """Test convert_set directly with different type arguments."""
    # Test with int type
    int_result = convert_set((int,), ["1", 2, 3.0], None)
    assert int_result == {1, 2, 3}
    assert all(isinstance(x, int) for x in int_result)

    # Test with float type
    float_result = convert_set((float,), ["1.5", 2, 3.0], None)
    assert float_result == {1.5, 2.0, 3.0}
    assert all(isinstance(x, float) for x in float_result)

    # Test with bool type
    bool_result = convert_set((bool,), ["yes", "no", 1, 0, True, False], None)
    assert bool_result == {True, False}

    # Test with Any type
    any_result = convert_set((Any,), ["text", 42, 3.14, True], None)
    assert any_result == {"text", 42, 3.14, True}

    # Test with unknown type (fallback case)
    class CustomType:
        pass

    fallback_result = convert_set((CustomType,), ["a", "b", "c"], None)
    assert fallback_result == {"a", "b", "c"}


def test_large_set_deduplication():
    """Test set deduplication with many duplicate items."""
    toml_content = """
    str_set = ["item1", "item2", "item1", "item3", "item2", "item4", "item1", "item5"]
    int_set = [1, 2, 3, 1, 2, 3, 4, 5, 1, 2, 3]
    float_set = []
    bool_set = []
    any_set = []
    empty_set = []
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetTypesConfig, f.name).validate()

        assert config.str_set == {"item1", "item2", "item3", "item4", "item5"}
        assert config.int_set == {1, 2, 3, 4, 5}


def test_nested_config_with_sets():
    """Test nested configuration models containing sets."""
    toml_content = """
    [[configs]]
    name = "service1"
    tags = ["web", "api", "public", "web"]

    [[configs]]
    name = "service2"
    tags = ["backend", "private", "api", "backend"]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(ConfigWithNestedSets, f.name).validate()

        assert len(config.configs) == 2
        assert config.configs[0].tags == {"web", "api", "public"}
        assert config.configs[1].tags == {"backend", "private", "api"}


def test_set_default_value():
    """Test default value for set when not provided."""

    class SetWithDefaultConfig(BaseConfigModel):
        required_set: set[str]
        optional_set: set[str] = {"default1", "default2"}

    toml_content = """
    required_set = ["item1", "item2"]
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()

        config = TomlEv(SetWithDefaultConfig, f.name).validate()

        assert config.required_set == {"item1", "item2"}
        assert config.optional_set == {"default1", "default2"}
