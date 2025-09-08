from tomlev import BaseConfigModel


class BooleanTestConfig(BaseConfigModel):
    simple_bool: bool
    bool_list: list[bool]
    bool_dict: dict[str, bool]


def test_python_standard_true_values():
    """Test all Python standard true values (from distutils.util.strtobool)"""

    # Test Python standard true values: 'y', 'yes', 't', 'true', 'on', '1'
    true_values = ["y", "yes", "t", "true", "on", "1"]

    for value in true_values:
        config = BooleanTestConfig(simple_bool=value)
        assert config.simple_bool is True, f"'{value}' should be True"

        # Test case insensitive
        config_upper = BooleanTestConfig(simple_bool=value.upper())
        assert config_upper.simple_bool is True, f"'{value.upper()}' should be True"

        # Test mixed case
        if len(value) > 1:
            config_mixed = BooleanTestConfig(simple_bool=value.capitalize())
            assert config_mixed.simple_bool is True, f"'{value.capitalize()}' should be True"


def test_additional_true_values():
    """Test edge cases with Python standard values"""

    # Test that we handle all the standard Python boolean true values correctly
    # This test ensures we're following distutils.util.strtobool conventions exactly
    config_t = BooleanTestConfig(simple_bool="t")
    assert config_t.simple_bool is True

    config_T = BooleanTestConfig(simple_bool="T")
    assert config_T.simple_bool is True


def test_false_values():
    """Test values that should evaluate to False"""

    # These are NOT in the true values set, so should be False
    false_values = ["n", "no", "f", "false", "off", "0", "enabled", "disabled", "invalid", ""]

    for value in false_values:
        config = BooleanTestConfig(simple_bool=value)
        assert config.simple_bool is False, f"'{value}' should be False"


def test_boolean_in_lists():
    """Test boolean conversion in list types"""

    config_data = {
        "simple_bool": True,
        "bool_list": ["true", "false", "yes", "no", "1", "0", "t", "f"],
        "bool_dict": {},
    }

    config = BooleanTestConfig(**config_data)

    expected = [True, False, True, False, True, False, True, False]
    assert config.bool_list == expected

    # Verify types are actually boolean
    assert all(isinstance(item, bool) for item in config.bool_list)


def test_boolean_in_dicts():
    """Test boolean conversion in dict value types"""

    config_data = {
        "simple_bool": True,
        "bool_list": [],
        "bool_dict": {
            "feature_a": "true",
            "feature_b": "false",
            "feature_c": "yes",
            "feature_d": "no",
            "feature_e": "1",
            "feature_f": "0",
            "feature_g": "t",
            "feature_h": "f",
        },
    }

    config = BooleanTestConfig(**config_data)

    expected = {
        "feature_a": True,
        "feature_b": False,
        "feature_c": True,
        "feature_d": False,
        "feature_e": True,
        "feature_f": False,
        "feature_g": True,
        "feature_h": False,
    }

    assert config.bool_dict == expected

    # Verify types are actually boolean
    assert all(isinstance(v, bool) for v in config.bool_dict.values())


def test_already_boolean_values():
    """Test that actual boolean values are preserved"""

    config = BooleanTestConfig(simple_bool=True, bool_list=[True, False], bool_dict={"key": True})

    assert config.simple_bool is True
    assert config.bool_list == [True, False]
    assert config.bool_dict == {"key": True}


def test_case_insensitive_behavior():
    """Test comprehensive case-insensitive behavior"""

    test_cases = [
        ("TRUE", True),
        ("True", True),
        ("true", True),
        ("YES", True),
        ("Yes", True),
        ("yes", True),
        ("Y", True),
        ("y", True),
        ("T", True),
        ("t", True),
        ("ON", True),
        ("On", True),
        ("on", True),
        ("1", True),
        ("FALSE", False),
        ("False", False),
        ("false", False),
        ("NO", False),
        ("No", False),
        ("no", False),
        ("0", False),
        ("disabled", False),
        ("DISABLED", False),
        ("", False),
    ]

    for value, expected in test_cases:
        config = BooleanTestConfig(simple_bool=value)
        assert config.simple_bool is expected, f"'{value}' should be {expected}"


def test_non_string_boolean_conversion():
    """Test conversion of non-string values to boolean"""

    # Test integer values
    config_int_1 = BooleanTestConfig(simple_bool=1)
    assert config_int_1.simple_bool is True

    config_int_0 = BooleanTestConfig(simple_bool=0)
    assert config_int_0.simple_bool is False

    # Test other truthy/falsy values
    config_list = BooleanTestConfig(simple_bool=[1, 2, 3])
    assert config_list.simple_bool is True

    config_empty_list = BooleanTestConfig(simple_bool=[])
    assert config_empty_list.simple_bool is False


def test_edge_cases():
    """Test edge cases and boundary conditions"""

    # Test None value (should default to empty string for bool)
    config = BooleanTestConfig()
    assert config.simple_bool is False  # Empty string default converts to False

    # Test whitespace values
    config_whitespace = BooleanTestConfig(simple_bool="  true  ")
    # Note: This might fail if whitespace isn't stripped - depends on implementation
    # The current implementation doesn't strip whitespace, so this should be False
    assert config_whitespace.simple_bool is False
