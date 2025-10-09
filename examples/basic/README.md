# Basic TomlEv Usage Example

This example demonstrates the basic usage of TomlEv for configuration management.

## Files

- `config.toml` - Main configuration file with environment variable placeholders
- `.env` - Environment variables file
- `app.py` - Example application using TomlEv

## Running the Example

```bash
# Install tomlev
pip install tomlev

# Run the example
python app.py
```

## What This Example Shows

- Loading configuration from TOML files
- Environment variable substitution with defaults
- Type-safe configuration access
- Automatic type conversion (int, bool, etc.)
