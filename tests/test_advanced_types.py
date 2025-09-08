from typing import Any

from tomlev import BaseConfigModel


class AdvancedTypesConfig(BaseConfigModel):
    # Complex nested types
    list_of_dicts: list[dict[str, Any]]
    list_of_str_dicts: list[dict[str, str]]
    list_of_int_dicts: list[dict[str, int]]

    # Numeric type conversion edge cases
    int_from_float: int
    float_from_int: float
    int_from_string: int
    float_from_string: float

    # Mixed type scenarios
    mixed_list: list[Any]
    any_field: Any


def test_list_of_dictionaries():
    """Test lists containing dictionaries with various value types"""

    config_data = {
        "list_of_dicts": [{"name": "alice", "age": 30, "active": True}, {"name": "bob", "age": 25, "active": False}],
        "list_of_str_dicts": [{"key1": "value1", "key2": "value2"}, {"key3": "value3", "key4": "value4"}],
        "list_of_int_dicts": [
            {"count": "10", "total": "20"},  # Strings that should convert to int
            {"count": 15, "total": 25},  # Already integers
        ],
        "int_from_float": 3.7,
        "float_from_int": 42,
        "int_from_string": "123",
        "float_from_string": "45.67",
        "mixed_list": ["string", 123, True, 45.6],
        "any_field": {"complex": "object"},
    }

    config = AdvancedTypesConfig(**config_data)

    # Test list of mixed dictionaries
    assert len(config.list_of_dicts) == 2
    assert config.list_of_dicts[0] == {"name": "alice", "age": 30, "active": True}
    assert config.list_of_dicts[1] == {"name": "bob", "age": 25, "active": False}

    # Test list of string dictionaries
    assert len(config.list_of_str_dicts) == 2
    assert config.list_of_str_dicts[0] == {"key1": "value1", "key2": "value2"}

    # Test list of int dictionaries with type conversion
    assert len(config.list_of_int_dicts) == 2
    assert config.list_of_int_dicts[0] == {"count": 10, "total": 20}
    assert config.list_of_int_dicts[1] == {"count": 15, "total": 25}
    assert all(isinstance(v, int) for d in config.list_of_int_dicts for v in d.values())


def test_numeric_type_conversions():
    """Test various numeric type conversion scenarios"""

    config_data = {
        "list_of_dicts": [],
        "list_of_str_dicts": [],
        "list_of_int_dicts": [],
        "int_from_float": 3.9,  # Should truncate to 3
        "float_from_int": 42,  # Should convert to 42.0
        "int_from_string": "789",  # Should parse to 789
        "float_from_string": "12.34",  # Should parse to 12.34
        "mixed_list": [],
        "any_field": None,
    }

    config = AdvancedTypesConfig(**config_data)

    # Test numeric conversions
    assert isinstance(config.int_from_float, int)
    assert config.int_from_float == 3

    assert isinstance(config.float_from_int, float)
    assert config.float_from_int == 42.0

    assert isinstance(config.int_from_string, int)
    assert config.int_from_string == 789

    assert isinstance(config.float_from_string, float)
    assert config.float_from_string == 12.34


def test_nested_dict_in_list_edge_cases():
    """Test edge cases with nested dictionaries in lists"""

    config_data = {
        "list_of_dicts": [{}],  # Empty dict
        "list_of_str_dicts": [{"empty_value": ""}],  # Empty string value
        "list_of_int_dicts": [{"zero": 0, "negative": -5}],  # Zero and negative
        "int_from_float": 0.0,
        "float_from_int": 0,
        "int_from_string": "0",
        "float_from_string": "0.0",
        "mixed_list": [None, "", 0, False],  # Falsy values
        "any_field": [],
    }

    config = AdvancedTypesConfig(**config_data)

    # Test empty and edge case values
    assert config.list_of_dicts == [{}]
    assert config.list_of_str_dicts == [{"empty_value": ""}]
    assert config.list_of_int_dicts == [{"zero": 0, "negative": -5}]

    # Test zero conversions
    assert config.int_from_float == 0
    assert config.float_from_int == 0.0
    assert config.int_from_string == 0
    assert config.float_from_string == 0.0


def test_error_handling_for_invalid_conversions():
    """Test that invalid type conversions raise appropriate errors"""

    import pytest

    # Test invalid int conversion
    with pytest.raises(ValueError):
        AdvancedTypesConfig(
            list_of_dicts=[],
            list_of_str_dicts=[],
            list_of_int_dicts=[],
            int_from_float=0,
            float_from_int=0,
            int_from_string="not_a_number",  # This should fail
            float_from_string="0.0",
            mixed_list=[],
            any_field=None,
        )

    # Test invalid float conversion
    with pytest.raises(ValueError):
        AdvancedTypesConfig(
            list_of_dicts=[],
            list_of_str_dicts=[],
            list_of_int_dicts=[],
            int_from_float=0,
            float_from_int=0,
            int_from_string="0",
            float_from_string="not_a_float",  # This should fail
            mixed_list=[],
            any_field=None,
        )


def test_empty_collections():
    """Test handling of empty collections"""

    config = AdvancedTypesConfig()

    # All collections should default to empty
    assert config.list_of_dicts == []
    assert config.list_of_str_dicts == []
    assert config.list_of_int_dicts == []
    assert config.mixed_list == []

    # Numeric fields should have default values
    assert config.int_from_float == 0
    assert config.float_from_int == 0.0
    assert config.int_from_string == 0
    assert config.float_from_string == 0.0
