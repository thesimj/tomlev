import os
import tempfile

import pytest

from tomlev import BaseConfigModel, ConfigValidationError, TomlEv


class EdgeCaseConfig(BaseConfigModel):
    name: str
    port: int
    debug: bool


def test_strict_mode_with_dotenv_duplicates():
    """Test strict mode behavior with duplicate .env variables"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("VAR1=value1\nVAR1=value2\n")  # Duplicate variable
        env_file = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "test"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        # Should raise error in strict mode
        with pytest.raises(ConfigValidationError, match="Strict mode enabled, variables.*defined several times"):
            TomlEv(EdgeCaseConfig, toml_file, env_file, strict=True)
    finally:
        os.unlink(env_file)
        os.unlink(toml_file)


def test_strict_mode_with_missing_variables():
    """Test strict mode with missing environment variables"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "$NONEXISTENT_VAR"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        # Should raise error in strict mode
        with pytest.raises(ConfigValidationError, match="Strict mode enabled, variables.*are not defined"):
            TomlEv(EdgeCaseConfig, toml_file, None, strict=True)
    finally:
        os.unlink(toml_file)


def test_non_strict_mode_with_missing_variables():
    """Test non-strict mode with missing environment variables"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "$NONEXISTENT_VAR"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        # Should work in non-strict mode, keeping the literal value
        config = TomlEv(EdgeCaseConfig, toml_file, None, strict=False).validate()
        assert config.name == "$NONEXISTENT_VAR"
    finally:
        os.unlink(toml_file)


def test_variable_expansion_with_defaults():
    """Test variable expansion with default values"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("""
name = "${APP_NAME|-default_app}"
port = "${PORT|-8080}"
debug = "${DEBUG|-false}"
""")
        toml_file = f.name

    try:
        # Without env vars, should use defaults
        config = TomlEv(EdgeCaseConfig, toml_file, None, strict=False).validate()
        assert config.name == "default_app"
        assert config.port == 8080
        assert config.debug is False
    finally:
        os.unlink(toml_file)


def test_expandvars_in_dotenv():
    """Test that environment variables are expanded in .env files"""
    old_val = os.environ.get("TEST_EXPAND")
    os.environ["TEST_EXPAND"] = "expanded"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("MY_VAR=${TEST_EXPAND}_value\n")
        env_file = f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "${MY_VAR}"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        config = TomlEv(EdgeCaseConfig, toml_file, env_file, strict=False).validate()
        assert config.name == "expanded_value"
    finally:
        os.unlink(env_file)
        os.unlink(toml_file)
        if old_val is None:
            os.environ.pop("TEST_EXPAND", None)
        else:
            os.environ["TEST_EXPAND"] = old_val


def test_include_environment_false():
    """Test with include_environment=False"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "test"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        env = TomlEv(EdgeCaseConfig, toml_file, None, include_environment=False)
        # Should not include system environment variables
        assert "PATH" not in env.environ

        config = env.validate()
        assert config.name == "test"
    finally:
        os.unlink(toml_file)


def test_tomlev_strict_disable_env_var():
    """Test TOMLEV_STRICT_DISABLE environment variable"""
    old_value = os.environ.get("TOMLEV_STRICT_DISABLE")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "$MISSING_VAR"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        # Set env var to disable strict mode
        os.environ["TOMLEV_STRICT_DISABLE"] = "true"

        # Should not raise error even with undefined variable
        env = TomlEv(EdgeCaseConfig, toml_file, None, strict=True)
        assert env.strict is False

        config = env.validate()
        assert config.name == "$MISSING_VAR"

    finally:
        os.unlink(toml_file)
        if old_value is None:
            os.environ.pop("TOMLEV_STRICT_DISABLE", None)
        else:
            os.environ["TOMLEV_STRICT_DISABLE"] = old_value


def test_tomlev_strict_disable_various_values():
    """Test various values for TOMLEV_STRICT_DISABLE"""
    old_value = os.environ.get("TOMLEV_STRICT_DISABLE")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "test"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        test_cases = [
            ("true", False),
            ("1", False),
            ("yes", False),
            ("y", False),
            ("on", False),
            ("false", True),
            ("0", True),
            ("anything_else", True),
        ]

        for env_val, expected_strict in test_cases:
            os.environ["TOMLEV_STRICT_DISABLE"] = env_val
            env = TomlEv(EdgeCaseConfig, toml_file, None, strict=True)
            assert env.strict is expected_strict

    finally:
        os.unlink(toml_file)
        if old_value is None:
            os.environ.pop("TOMLEV_STRICT_DISABLE", None)
        else:
            os.environ["TOMLEV_STRICT_DISABLE"] = old_value


def test_empty_toml_file():
    """Test with empty TOML file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("")  # Empty file
        toml_file = f.name

    try:
        # Should use default values from the model
        config = TomlEv(EdgeCaseConfig, toml_file, None).validate()
        assert config.name == ""  # Default str
        assert config.port == 0  # Default int
        assert config.debug is False  # Default bool
    finally:
        os.unlink(toml_file)


def test_nonexistent_dotenv_file():
    """Test behavior when .env file doesn't exist"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "test"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        # Should work fine when .env doesn't exist
        config = TomlEv(EdgeCaseConfig, toml_file, "/nonexistent/path/.env").validate()
        assert config.name == "test"
        assert config.port == 8080
        assert config.debug is False
    finally:
        os.unlink(toml_file)


def test_comment_removal():
    """Test that comments are properly removed from TOML"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write("""# This is a comment
name = "test"  # inline comment
# Another comment
port = 8080
debug = false
""")
        toml_file = f.name

    try:
        config = TomlEv(EdgeCaseConfig, toml_file, None).validate()
        assert config.name == "test"
        assert config.port == 8080
        assert config.debug is False
    finally:
        os.unlink(toml_file)


def test_undefined_variable_raises_config_validation_error():
    """Test that undefined variables raise ConfigValidationError not ValueError"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "$NOT_DEFINED"\nport = 8080\ndebug = false')
        toml_file = f.name

    try:
        # Should raise ConfigValidationError in strict mode
        with pytest.raises(ConfigValidationError, match="variables.*are not defined"):
            TomlEv(EdgeCaseConfig, toml_file, None, strict=True)
    finally:
        os.unlink(toml_file)
