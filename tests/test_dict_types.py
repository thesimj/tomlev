from tomlev import BaseConfigModel


class DictTypesConfig(BaseConfigModel):
    str_dict: dict[str, str]
    int_dict: dict[str, int]
    float_dict: dict[str, float]
    bool_dict: dict[str, bool]
    plain_dict: dict
    empty_dict: dict[str, str]


def test_dict_types():
    """Test different dict types: str, int, float, bool, and plain dict"""

    # Create test configuration
    config_data = {
        "str_dict": {"key1": "value1", "key2": "value2"},
        "int_dict": {"num1": 42, "num2": 100},
        "float_dict": {"pi": 3.14, "e": 2.71},
        "bool_dict": {"enabled": "true", "disabled": "false", "on": "1", "off": "0"},
        "plain_dict": {"any": "value", "number": 123, "bool": True},
        "empty_dict": {},
    }

    # Create config object
    config = DictTypesConfig(**config_data)

    # Assert string dict
    assert config.str_dict == {"key1": "value1", "key2": "value2"}
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in config.str_dict.items())

    # Assert int dict
    assert config.int_dict == {"num1": 42, "num2": 100}
    assert all(isinstance(k, str) and isinstance(v, int) for k, v in config.int_dict.items())

    # Assert float dict
    assert config.float_dict == {"pi": 3.14, "e": 2.71}
    assert all(isinstance(k, str) and isinstance(v, float) for k, v in config.float_dict.items())

    # Assert bool dict
    expected_bools = {"enabled": True, "disabled": False, "on": True, "off": False}
    assert config.bool_dict == expected_bools
    assert all(isinstance(k, str) and isinstance(v, bool) for k, v in config.bool_dict.items())

    # Assert plain dict (no type conversion)
    assert config.plain_dict == {"any": "value", "number": 123, "bool": True}

    # Assert empty dict
    assert config.empty_dict == {}
    assert isinstance(config.empty_dict, dict)


def test_dict_type_conversion():
    """Test that dict values are properly converted to their target types"""

    config_data = {
        "str_dict": {"num": 123, "bool": True, "float": 45.6},  # Mixed types converted to str
        "int_dict": {"ten": "10", "twenty": "20"},  # Strings converted to int
        "float_dict": {"pi": "3.14", "int": 42},  # Mixed types converted to float
        "bool_dict": {"true1": "TRUE", "false1": "False", "true2": "1", "false2": "0"},  # Various bool representations
        "plain_dict": {"mixed": "values", "number": 42, "bool": False},  # No conversion
        "empty_dict": {},
    }

    config = DictTypesConfig(**config_data)

    # String dict should convert all values to strings
    assert config.str_dict == {"num": "123", "bool": "True", "float": "45.6"}

    # Int dict should convert string numbers to integers
    assert config.int_dict == {"ten": 10, "twenty": 20}

    # Float dict should convert to floats
    assert config.float_dict == {"pi": 3.14, "int": 42.0}

    # Bool dict should handle various representations
    assert config.bool_dict == {"true1": True, "false1": False, "true2": True, "false2": False}

    # Plain dict should preserve original types
    assert config.plain_dict == {"mixed": "values", "number": 42, "bool": False}


def test_empty_and_missing_dicts():
    """Test handling of empty and missing dict fields"""

    # Test with missing dicts (should default to empty)
    config = DictTypesConfig()

    assert config.str_dict == {}
    assert config.int_dict == {}
    assert config.float_dict == {}
    assert config.bool_dict == {}
    assert config.plain_dict == {}
    assert config.empty_dict == {}
