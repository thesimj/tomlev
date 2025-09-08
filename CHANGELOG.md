# Changelog

All notable changes to TomlEv will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-01-09

### Fixed

- **Breaking**: Error handling now uses `ConfigValidationError` instead of `ValueError` for configuration validation
  errors
- Undefined environment variable errors in strict mode now raise appropriate `ConfigValidationError`
- Consistent exception handling across the entire codebase for configuration-related errors

### Added

- New test case `test_undefined_variable_raises_config_validation_error` to ensure proper exception handling
- Multi-platform quality checks now run on Ubuntu, Windows, and macOS in CI/CD pipeline
- Comprehensive workflow documentation with detailed job descriptions and dependency explanations
- TDD (Test-Driven Development) workflow documentation
- Comprehensive quality check enforcement in development workflow

### Enhanced

- **CI/CD Pipeline Improvements**:
    - Mandatory quality gates with `continue-on-error: false` on all critical steps
    - Quality checks achieve 100% success rate requirement before deployment
    - Cross-platform cache handling for Windows vs Unix systems
    - Enhanced job dependencies ensuring no deployment without quality validation
    - Improved workflow structure with clear documentation and failure handling
- Better error messages and validation consistency throughout the library
- Test coverage for edge cases in strict mode validation

### Changed

- GitHub Actions workflow now enforces mandatory quality checks across all platforms
- Quality checks must pass on Ubuntu, Windows, and macOS before package building
- CI/CD pipeline structure enhanced with explicit job dependencies and failure conditions
- Development workflow now mandates running `uv run scripts/quality_check.py` after any code changes
- Enhanced development guidelines with mandatory quality assurance requirements

## [1.0.0] - 2025-01-09

### Added

- Comprehensive Google-style docstrings for all public APIs (100% coverage)
- Security scanning with Bandit and dependency vulnerability checks
- Property-based testing with Hypothesis for robust edge case testing
- Performance benchmarking with pytest-benchmark (8 comprehensive benchmarks)
- Code complexity analysis with Radon (average grade: B)
- Docstring coverage checking with automated validation
- Community contribution guidelines (CONTRIBUTING.md)
- Security policy documentation (SECURITY.md)
- Enhanced PyPI package metadata with complete classifiers
- Support for additional development dependency groups (security, quality)
- Automated quality check script with comprehensive validation
- GitHub issue templates for bug reports and feature requests
- **Python 3.11+ Features**: Leveraged latest Python features including:
    - Structural pattern matching for improved type conversion logic
    - Modern type hints with PEP 585 built-in generics
    - Enhanced exception handling with better error reporting
    - TypeAlias for improved code clarity
- **Type Safety Enhancements**:
    - Support for `get_type_hints()` to resolve string annotations
    - Improved handling of `from __future__ import annotations`
    - Better generic type support for complex nested structures
    - Enhanced boolean conversion with comprehensive value recognition
- **Modern Package Structure**:
    - Added `py.typed` marker file for PEP 561 compliance
    - Enhanced mypy configuration with strict mode
    - Improved package metadata and classifiers
    - Modern dependency management with uv

### Enhanced

- Improved type safety with strict mypy configuration (zero type errors)
- Better error messages and validation feedback
- Enhanced pytest configuration with custom markers and 95%+ test coverage
- Modernized CI/CD pipeline with additional quality checks
- Updated package dependencies with compatible versions
- Improved code formatting compliance (100% ruff compliant)

### Fixed

- Unicode encoding issues in quality check script for Windows compatibility
- Missing docstrings for private methods improving documentation completeness
- Bandit security warnings for legitimate assert usage in validation code
- Property-based test failures with special characters and encoding issues
- Benchmark test TOML syntax errors and nested configuration issues
- Dependency conflicts between security and quality tool packages
- Boolean conversion now properly handles string values from TOML substitution
- Resolved compatibility issues with string type annotations
- Fixed pattern matching logic for complex type conversions
- Improved error handling in strict mode validation

### Changed

- **Breaking**: Requires Python 3.11 or later
- Modernized type hints throughout the codebase
- Improved code organization with type aliases
- Enhanced documentation with comprehensive examples
- Refactored BaseConfigModel with structural pattern matching

### Removed

- Support for Python versions below 3.11

### Security

- Added automated security scanning with Bandit (zero security issues)
- Implemented dependency vulnerability scanning with Safety
- Enhanced input validation and error handling
- Added security best practices documentation
- Proper handling of assert statements in validation code with security annotations
- Enhanced input validation and type checking
- Improved error handling for malformed configuration files
- Better validation of environment variable substitution

## [0.9.x] - Previous Releases

For information about releases prior to 1.0.0a1, please refer to
the [GitHub Releases](https://github.com/thesimj/tomlev/releases) page.

---

## Release Notes Format

### Types of Changes

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes
- **Enhanced** for improvements to existing features

### Version Numbering

- **Major version** (X.0.0): Breaking changes, new major features
- **Minor version** (X.Y.0): New features, backwards compatible
- **Patch version** (X.Y.Z): Bug fixes, backwards compatible
- **Pre-release** (X.Y.Z-alpha/beta/rc): Testing releases

### Contributing to Changelog

- Follow the established format and categorization
- Include relevant issue/PR numbers when applicable
- Move entries to a versioned section upon release
