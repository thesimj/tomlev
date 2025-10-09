# TomlEv Examples

This directory contains practical examples demonstrating various TomlEv features and use cases.

## Directory Structure

- **basic/** - Simple configuration loading with environment variables
- **advanced/** - Complex configs with includes, custom types, and nested structures
- **integrations/** - Framework integration examples (FastAPI, etc.)

## Quick Start

Each example is self-contained with its own README. To run an example:

```bash
cd examples/basic
python app.py
```

## Examples Overview

### Basic Example
**Location:** `basic/`

Learn the fundamentals:
- Loading TOML configuration files
- Environment variable substitution with `${VAR|-default}` syntax
- Type-safe configuration models
- Automatic type conversion (str, int, bool, float)

### Advanced Example
**Location:** `advanced/`

Master advanced features:
- **Config Includes**: Using `__include` to compose from multiple files
- **Complex Types**: Lists, dicts, sets, tuples
- **Nested Models**: Multi-level configuration hierarchy
- **Enums**: Type-safe enumeration values
- **Default Values**: Class-level and type-based defaults

### Integration Examples
**Location:** `integrations/`

See TomlEv in action:
- **FastAPI**: Web API configuration with dependency injection
- Configuration singleton pattern
- Environment-specific settings
- CORS, database, and security configs

## Learning Path

1. **Start with Basic** - Understand core concepts
2. **Move to Advanced** - Learn powerful features
3. **Explore Integrations** - See real-world usage patterns

## Documentation

For complete documentation, visit the [main README](../README.md).

## Contributing

Have a useful example? Feel free to contribute! Examples should be:
- Self-contained and runnable
- Well-documented with comments
- Focused on a specific feature or use case
- Include a README explaining what it demonstrates
