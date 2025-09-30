# Advanced TomlEv Usage Example

This example demonstrates advanced TomlEv features including config file includes, custom types, and complex data structures.

## Files

- `main.toml` - Main configuration file with __include directives
- `database.toml` - Separate database configuration
- `features.toml` - Feature flags configuration
- `.env` - Environment variables
- `app.py` - Example application

## Running the Example

```bash
python app.py
```

## What This Example Shows

- **Config Includes**: Using `__include` to compose configs from multiple files
- **Complex Types**: Lists, dictionaries, sets, tuples
- **Nested Configs**: Multi-level configuration hierarchy
- **Enums**: Using Python enums for type-safe values
- **Default Values**: Class-level defaults
