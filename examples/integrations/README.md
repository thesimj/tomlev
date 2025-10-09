# TomlEv Integration Examples

This directory contains examples of integrating TomlEv with popular Python frameworks.

## FastAPI Integration

Demonstrates how to use TomlEv for FastAPI application configuration.

### Files

- `fastapi_app.py` - FastAPI application with TomlEv configuration
- `config.toml` - Application configuration
- `.env` - Environment variables

### Running

```bash
# Install dependencies
pip install tomlev fastapi uvicorn

# Run the application
python fastapi_app.py
```

Visit `http://localhost:8000/docs` for the API documentation.

## What This Shows

- FastAPI dependency injection with TomlEv
- Configuration singleton pattern
- Environment-specific settings
- Type-safe API configuration
