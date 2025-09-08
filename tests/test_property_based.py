"""Property-based tests for TomlEv using Hypothesis.

These tests use property-based testing to verify that TomlEv behaves correctly
across a wide range of inputs and edge cases that might not be covered by
traditional unit tests.
"""

from __future__ import annotations

import tempfile
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tomlev import BaseConfigModel, TomlEv


class PropertyTestConfig(BaseConfigModel):
    """Test configuration model for property-based tests."""

    name: str
    count: int
    enabled: bool
    ratio: float
    tags: list[str]
    metadata: dict[str, Any]


@pytest.mark.hypothesis
class TestPropertyBasedValidation:
    """Property-based tests for configuration validation."""

    @given(
        name=st.text(min_size=1),
        count=st.integers(min_value=0),
        enabled=st.booleans(),
        ratio=st.floats(min_value=0.0, max_value=1.0),
        tags=st.lists(st.text(min_size=1), min_size=0, max_size=10),
        metadata=st.dictionaries(
            st.text(min_size=1, max_size=20), st.one_of(st.text(), st.integers(), st.floats()), min_size=0, max_size=5
        ),
    )
    def test_config_model_roundtrip(
        self, name: str, count: int, enabled: bool, ratio: float, tags: list[str], metadata: dict[str, Any]
    ) -> None:
        """Test that configuration models preserve data through roundtrip conversion."""
        # Create configuration with generated data
        config_data = {
            "name": name,
            "count": count,
            "enabled": enabled,
            "ratio": ratio,
            "tags": tags,
            "metadata": metadata,
        }

        # Create and validate configuration
        config = PropertyTestConfig(**config_data)

        # Verify all values are preserved and properly typed
        assert config.name == name
        assert config.count == count
        assert config.enabled == enabled
        assert config.ratio == ratio
        assert config.tags == tags
        assert config.metadata == metadata

        # Verify types
        assert isinstance(config.name, str)
        assert isinstance(config.count, int)
        assert isinstance(config.enabled, bool)
        assert isinstance(config.ratio, float)
        assert isinstance(config.tags, list)
        assert isinstance(config.metadata, dict)

    @given(
        bool_values=st.lists(
            st.one_of(
                st.booleans(),
                st.sampled_from(["true", "false", "True", "False", "1", "0", "yes", "no", "y", "n", "on", "off"]),
                st.integers(),
                st.floats(),
            ),
            min_size=1,
            max_size=20,
        )
    )
    def test_boolean_conversion_properties(self, bool_values: list[Any]) -> None:
        """Test boolean conversion invariants across various input types."""

        class BoolListConfig(BaseConfigModel):
            flags: list[bool]

        config = BoolListConfig(flags=bool_values)

        # All values should be converted to booleans
        assert all(isinstance(flag, bool) for flag in config.flags)
        assert len(config.flags) == len(bool_values)

        # String boolean conversion should be case-insensitive and predictable
        for original, converted in zip(bool_values, config.flags):
            if isinstance(original, str):
                expected = original.lower() in {"true", "1", "yes", "y", "on", "t"}
                assert converted == expected, f"Failed for {original!r}: expected {expected}, got {converted}"

    @given(
        numeric_strings=st.lists(
            st.one_of(
                st.integers().map(str),
                st.floats(allow_nan=False, allow_infinity=False).map(str),
                st.text(),  # Include non-numeric strings to test error handling
            ),
            min_size=0,
            max_size=10,
        )
    )
    def test_numeric_conversion_robustness(self, numeric_strings: list[str]) -> None:
        """Test that numeric conversion handles various string formats gracefully."""

        class NumericConfig(BaseConfigModel):
            values: list[str]  # Keep as strings to test the input

        # This should always succeed since we're keeping them as strings
        config = NumericConfig(values=numeric_strings)
        assert config.values == numeric_strings

        # Test individual conversions manually to verify robustness
        for value_str in numeric_strings:
            try:
                # Try int conversion
                int_val = int(value_str)
                assert isinstance(int_val, int)
            except ValueError:
                # Expected for non-numeric strings
                pass

            try:
                # Try float conversion
                float_val = float(value_str)
                assert isinstance(float_val, float)
            except ValueError:
                # Expected for non-numeric strings
                pass

    @given(
        config_data=st.fixed_dictionaries(
            {
                "host": st.text(
                    alphabet=st.characters(
                        min_codepoint=32,  # Space character
                        max_codepoint=126,  # Tilde character (printable ASCII)
                        blacklist_characters=['"', "'", "\\", "$"],
                    ),
                    min_size=1,
                    max_size=50,
                ),
                "port": st.integers(min_value=1, max_value=65535),
                "debug": st.booleans(),
            }
        )
    )
    def test_toml_loading_invariants(self, config_data: dict[str, Any]) -> None:
        """Test invariants that should hold for all valid TOML configurations."""

        class ServerConfig(BaseConfigModel):
            host: str
            port: int
            debug: bool

        # Create TOML content
        toml_content = f'''
host = "{config_data["host"]}"
port = {config_data["port"]}
debug = {str(config_data["debug"]).lower()}
'''

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            toml_file = f.name

        try:
            # Load configuration
            config = TomlEv(ServerConfig, toml_file, None).validate()

            # Verify invariants
            assert isinstance(config.host, str)
            assert isinstance(config.port, int)
            assert isinstance(config.debug, bool)

            # Values should match input
            assert config.host == config_data["host"]
            assert config.port == config_data["port"]
            assert config.debug == config_data["debug"]

        finally:
            # Cleanup
            import os

            os.unlink(toml_file)

    @given(
        nested_data=st.recursive(
            st.one_of(st.text(), st.integers(), st.booleans(), st.floats(allow_nan=False, allow_infinity=False)),
            lambda children: st.dictionaries(st.text(min_size=1, max_size=10), children, min_size=0, max_size=3),
            max_leaves=10,
        )
    )
    def test_nested_structure_preservation(self, nested_data: Any) -> None:
        """Test that nested data structures are preserved correctly."""

        class FlexibleConfig(BaseConfigModel):
            data: Any  # Using Any to allow flexible structure

        config = FlexibleConfig(data=nested_data)

        # Data should be preserved exactly
        assert config.data == nested_data

        # Type should be preserved
        assert type(config.data) is type(nested_data)


@pytest.mark.hypothesis
@pytest.mark.slow
class TestPropertyBasedEdgeCases:
    """Property-based tests for edge cases and error conditions."""

    @given(
        invalid_keys=st.lists(
            st.text().filter(lambda x: not x.isidentifier() or x.startswith("_")), min_size=1, max_size=5
        )
    )
    def test_invalid_attribute_names_rejected(self, invalid_keys: list[str]) -> None:
        """Test that invalid attribute names are properly rejected."""

        class StrictConfig(BaseConfigModel):
            valid_attr: str

        # Try to create config with invalid extra keys
        for invalid_key in invalid_keys:
            config_data = {"valid_attr": "test", invalid_key: "value"}

            # Should raise assertion error for unknown keys
            import re

            escaped_key = re.escape(invalid_key)
            with pytest.raises(AssertionError, match=f"{escaped_key} in config file but not in config model"):
                StrictConfig(**config_data)

    @given(empty_values=st.one_of(st.just(None), st.just(""), st.just([]), st.just({})))
    def test_empty_values_handling(self, empty_values: Any) -> None:
        """Test handling of various empty/null values."""

        class OptionalConfig(BaseConfigModel):
            optional_field: Any

        config = OptionalConfig(optional_field=empty_values)
        assert config.optional_field == empty_values
