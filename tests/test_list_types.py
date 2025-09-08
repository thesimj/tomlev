from tomlev import BaseConfigModel


class ListTypesConfig(BaseConfigModel):
    str_list: list[str]
    int_list: list[int]
    float_list: list[float]
    bool_list: list[bool]
    empty_list: list[str]
    plain_list: list  # Plain list type without generic parameters


def test_list_types():
    """Test different list types: str, int, float, bool, and empty lists"""

    # Create a test configuration
    config_data = {
        "str_list": ["hello", "world", "test"],
        "int_list": [1, 2, 3, 42],
        "float_list": [1.5, 2.7, 3.14],
        "bool_list": ["true", "false", "1", "0", "yes", "no"],
        "empty_list": [],
        "plain_list": ["mixed", 123, True, 45.6],  # Plain list with mixed types
    }

    # Create config object
    config = ListTypesConfig(**config_data)

    # Assert string list
    assert config.str_list == ["hello", "world", "test"]
    assert all(isinstance(item, str) for item in config.str_list)

    # Assert int list
    assert config.int_list == [1, 2, 3, 42]
    assert all(isinstance(item, int) for item in config.int_list)

    # Assert float list
    assert config.float_list == [1.5, 2.7, 3.14]
    assert all(isinstance(item, float) for item in config.float_list)

    # Assert bool list
    expected_bools = [True, False, True, False, True, False]
    assert config.bool_list == expected_bools
    assert all(isinstance(item, bool) for item in config.bool_list)

    # Assert an empty list
    assert config.empty_list == []
    assert isinstance(config.empty_list, list)

    # Assert plain list (converts all to strings by default)
    assert config.plain_list == ["mixed", "123", "True", "45.6"]
    assert all(isinstance(item, str) for item in config.plain_list)


def test_list_type_conversion():
    """Test that list items are properly converted to their target types"""

    config_data = {
        "str_list": [123, 45.6, True],  # Mixed types converted to str
        "int_list": ["10", "20", "30"],  # Strings converted to int
        "float_list": ["1.1", "2.2", 3],  # Mixed types converted to float
        "bool_list": ["TRUE", "False", "1", "0"],  # Various bool representations
        "empty_list": [],
        "plain_list": [1, 2, 3],  # Will be converted to strings
    }

    config = ListTypesConfig(**config_data)

    # String list should convert all items to strings
    assert config.str_list == ["123", "45.6", "True"]

    # Int list should convert string numbers to integers
    assert config.int_list == [10, 20, 30]

    # Float list should convert to floats
    assert config.float_list == [1.1, 2.2, 3.0]

    # Bool list should handle various representations
    assert config.bool_list == [True, False, True, False]

    # Plain list should convert to strings (default behavior)
    assert config.plain_list == ["1", "2", "3"]


def test_empty_and_missing_lists():
    """Test handling of empty and missing list fields"""

    # Test with missing lists (should default to empty)
    config = ListTypesConfig()

    assert config.str_list == []
    assert config.int_list == []
    assert config.float_list == []
    assert config.bool_list == []
    assert config.empty_list == []
    assert config.plain_list == []
