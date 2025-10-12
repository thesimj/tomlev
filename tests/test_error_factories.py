"""
Test error factory methods in tomlev/errors.py.

These tests ensure all error factory methods work correctly and produce
the expected error messages.
"""

from __future__ import annotations

from tomlev.errors import (
    ConfigValidationError,
    EnvironmentVariableError,
    IncludeError,
    TypeConversionError,
)

# =============================================================================
# ConfigValidationError Tests
# =============================================================================


def test_config_validation_error_basic() -> None:
    """Test ConfigValidationError with basic error."""
    error = ConfigValidationError([("field1", "error message")])

    assert len(error.errors) == 1
    assert error.errors[0] == ("field1", "error message")
    assert "field1" in str(error)
    assert "error message" in str(error)


def test_config_validation_error_multiple() -> None:
    """Test ConfigValidationError with multiple errors."""
    error = ConfigValidationError([("field1", "error1"), ("field2", "error2")])

    assert len(error.errors) == 2
    assert "field1" in str(error)
    assert "field2" in str(error)


# =============================================================================
# EnvironmentVariableError Tests
# =============================================================================


def test_environment_variable_error_missing_variables() -> None:
    """Test EnvironmentVariableError.missing_variables factory."""
    error = EnvironmentVariableError.missing_variables(["VAR1", "VAR2"])

    assert len(error.errors) == 1
    assert error.errors[0][0] == "environment_variables"
    assert "$VAR1" in error.errors[0][1]
    assert "$VAR2" in error.errors[0][1]
    assert "Strict mode enabled" in error.errors[0][1]
    assert "not defined" in error.errors[0][1]


def test_environment_variable_error_duplicate_variables() -> None:
    """Test EnvironmentVariableError.duplicate_variables factory."""
    error = EnvironmentVariableError.duplicate_variables(["DUP1", "DUP2"])

    assert len(error.errors) == 1
    assert error.errors[0][0] == "environment_variables"
    assert "$DUP1" in error.errors[0][1]
    assert "$DUP2" in error.errors[0][1]
    assert "Strict mode enabled" in error.errors[0][1]
    assert "defined several times" in error.errors[0][1]


# =============================================================================
# IncludeError Tests
# =============================================================================


def test_include_error_invalid_type() -> None:
    """Test IncludeError.invalid_type factory."""
    error = IncludeError.invalid_type()

    assert len(error.errors) == 1
    assert error.errors[0][0] == "include"
    assert "__include must be a string or list of strings" in error.errors[0][1]


def test_include_error_cycle_detected() -> None:
    """Test IncludeError.cycle_detected factory."""
    error = IncludeError.cycle_detected("/path/to/file.toml")

    assert len(error.errors) == 1
    assert error.errors[0][0] == "include"
    assert "Include cycle detected" in error.errors[0][1]
    assert "/path/to/file.toml" in error.errors[0][1]


def test_include_error_file_not_found() -> None:
    """Test IncludeError.file_not_found factory."""
    error = IncludeError.file_not_found("/path/to/missing.toml")

    assert len(error.errors) == 1
    assert error.errors[0][0] == "include"
    assert "Included TOML not found" in error.errors[0][1]
    assert "/path/to/missing.toml" in error.errors[0][1]


# =============================================================================
# TypeConversionError Tests
# =============================================================================


def test_type_conversion_error_invalid_type() -> None:
    """Test TypeConversionError.invalid_type factory."""
    error = TypeConversionError.invalid_type("field_name", "int", "str")

    assert len(error.errors) == 1
    assert error.errors[0][0] == "field_name"
    assert "Expected int" in error.errors[0][1]
    assert "got str" in error.errors[0][1]


def test_type_conversion_error_invalid_literal() -> None:
    """Test TypeConversionError.invalid_literal factory."""
    error = TypeConversionError.invalid_literal("status", "invalid", ["active", "inactive", "pending"])

    assert len(error.errors) == 1
    assert error.errors[0][0] == "status"
    assert "'invalid'" in error.errors[0][1]
    assert "not in allowed Literal" in error.errors[0][1]
    assert "active" in error.errors[0][1]
    assert "inactive" in error.errors[0][1]
    assert "pending" in error.errors[0][1]


def test_type_conversion_error_invalid_enum() -> None:
    """Test TypeConversionError.invalid_enum factory."""
    error = TypeConversionError.invalid_enum("color", "purple", "Color")

    assert len(error.errors) == 1
    assert error.errors[0][0] == "color"
    assert "Invalid value" in error.errors[0][1]
    assert "'purple'" in error.errors[0][1]
    assert "enum Color" in error.errors[0][1]


# =============================================================================
# Integration Tests
# =============================================================================


def test_error_exception_behavior() -> None:
    """Test that errors behave like proper exceptions."""
    error = ConfigValidationError([("test", "message")])

    # Test that it's an exception
    assert isinstance(error, Exception)

    # Test that it can be raised and caught
    try:
        raise error
    except ConfigValidationError as e:
        assert e.errors == [("test", "message")]


def test_error_inheritance() -> None:
    """Test that specialized errors inherit from ConfigValidationError."""
    # Test inheritance
    assert issubclass(EnvironmentVariableError, ConfigValidationError)
    assert issubclass(IncludeError, ConfigValidationError)
    assert issubclass(TypeConversionError, ConfigValidationError)

    # Test that specialized errors can be caught as ConfigValidationError
    try:
        raise EnvironmentVariableError.missing_variables(["TEST"])
    except ConfigValidationError as e:
        assert isinstance(e, EnvironmentVariableError)
