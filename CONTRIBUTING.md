# Contributing to TomlEv

Thank you for your interest in contributing to TomlEv! We welcome contributions of all kinds, from bug reports and
documentation improvements to feature implementations and performance optimizations.

## 🚀 Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/tomlev.git
   cd tomlev
   ```

2. **Set up the development environment**
   ```bash
   # Install uv (if not already installed)
   pip install uv

   # Install development dependencies
   uv sync --dev
   uv sync --group security
   uv sync --group quality
   ```

3. **Run tests to ensure everything works**
   ```bash
   uv run pytest
   ```

## 📋 Development Workflow

### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation changes
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Run the full test suite**
   ```bash
   # Code quality checks
   uv run ruff check
   uv run ruff format
   uv run mypy tomlev

   # Security scanning
   uv run bandit -r tomlev
   uv run safety check

   # Tests with coverage
   uv run pytest --cov --cov-fail-under=90

   # Documentation coverage
   uv run docstr-coverage tomlev
   ```

4. **Run pre-commit hooks**
   ```bash
   uv run pre-commit run --all-files
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

6. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🎯 Areas for Contribution

### High Priority

- **Performance optimizations** - Profile and improve parsing speed
- **Additional type support** - Extend type system capabilities
- **Documentation** - Examples, tutorials, API documentation
- **Error messages** - Improve error reporting and user experience

### Medium Priority

- **Plugins/Extensions** - Add support for custom validators
- **Integration tests** - Real-world usage scenarios
- **Benchmarks** - Performance regression testing
- **Developer tools** - Enhanced debugging capabilities

### Good First Issues

Look for issues labeled `good-first-issue` or `help-wanted` in our GitHub repository.

## 📝 Coding Standards

### Python Code Style

- **Formatter**: Ruff (line length: 120 characters)
- **Type Hints**: Required for all public APIs (mypy strict mode)
- **Docstrings**: Google style for all public functions/classes
- **Import Sorting**: Organized by ruff

### Documentation

- **API docs**: Comprehensive Google-style docstrings
- **Examples**: Include usage examples in docstrings
- **Type hints**: All public APIs must be fully typed
- **README updates**: Update examples when changing public APIs

### Testing

- **Coverage**: Minimum 90% test coverage required
- **Test types**: Unit, integration, property-based (Hypothesis)
- **Performance**: Include benchmark tests for performance-critical code
- **Edge cases**: Test error conditions and edge cases thoroughly

## 🧪 Testing Guidelines

### Test Structure

```python
# Test file naming: test_*.py
# Test function naming: test_*

class TestFeatureName:
    def test_happy_path_scenario(self):
        """Test normal usage scenarios."""
        pass

    def test_edge_case_scenario(self):
        """Test edge cases and error conditions."""
        pass

    @pytest.mark.benchmark
    def test_performance_benchmark(self):
        """Benchmark performance-critical operations."""
        pass
```

### Property-Based Testing

Use Hypothesis for testing complex scenarios:

```python
from hypothesis import given, strategies as st


@given(config_data=st.dictionaries(st.text(), st.text()))
def test_config_parsing_properties(config_data):
    """Property-based test for configuration parsing."""
    # Test invariants that should always hold
    pass
```

### Test Commands

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov --cov-report=html

# Run only fast tests
uv run pytest -m "not slow"

# Run benchmarks
uv run pytest -m benchmark --benchmark-only

# Run property-based tests
uv run pytest -m hypothesis
```

## 📚 Documentation Guidelines

### API Documentation

- Use Google-style docstrings
- Include examples for public functions
- Document all parameters, returns, and exceptions
- Add version information for new features

### Example Docstring

```python
def load_config(file_path: str, strict: bool = True) -> ConfigModel:
    """Load and validate configuration from a TOML file.

    Args:
        file_path: Path to the TOML configuration file.
        strict: Whether to enforce strict validation. Defaults to True.

    Returns:
        The validated configuration model instance.

    Raises:
        FileNotFoundError: When the configuration file doesn't exist.
        ValidationError: When configuration validation fails.

    Example:
        ```python
        config = load_config("app.toml", strict=False)
        print(f"Host: {config.host}")
        ```

    Note:
        This function requires Python 3.11+ for optimal performance.
    """
```

## 🔍 Code Review Process

### Pull Request Requirements

- [ ] **Tests**: All new code has corresponding tests
- [ ] **Documentation**: Public APIs are documented
- [ ] **Type hints**: All code is properly typed
- [ ] **Performance**: No significant performance regressions
- [ ] **Security**: Code has been reviewed for security issues
- [ ] **Backwards compatibility**: Changes maintain API compatibility

### Review Checklist

1. **Functionality**: Does the code work as intended?
2. **Design**: Is the solution well-designed and maintainable?
3. **Testing**: Are tests comprehensive and meaningful?
4. **Documentation**: Is the code and API properly documented?
5. **Performance**: Are there any performance implications?
6. **Security**: Are there any security concerns?

## 🐛 Reporting Issues

### Bug Reports

Use our bug report template and include:

- **TomlEv version** and Python version
- **Operating system** and relevant environment details
- **Minimal reproduction case**
- **Expected vs actual behavior**
- **Error messages or stack traces**

### Feature Requests

Use our feature request template and include:

- **Problem description** - What problem does this solve?
- **Proposed solution** - How should this work?
- **Alternatives considered** - What other approaches were considered?
- **Additional context** - Any other relevant information

## 🎉 Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Respect different viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, discussions
- **Pull Requests**: Code contributions and reviews
- **Email**: Security vulnerabilities (m+security@bubelich.com)

## 🏆 Recognition

Contributors are recognized in:

- **Release notes** for significant contributions
- **README.md** contributor section
- **GitHub repository** contributor statistics

## 📄 License

By contributing to TomlEv, you agree that your contributions will be licensed under the same MIT License that covers the
project.

---

**Thank you for contributing to TomlEv!** 🎉

Your contributions help make configuration management better for Python developers everywhere.
