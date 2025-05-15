<h2>
    <p style="text-align: center;">
        TomlEv - Open-source Python framework to manage environment variables
    </p>
</h2>

---
[![Latest Version](https://badgen.net/pypi/v/tomlev)](https://pypi.python.org/pypi/tomlev/)
[![Tomlev CI/CD Pipeline](https://github.com/thesimj/tomlev/actions/workflows/main.yml/badge.svg)](https://github.com/thesimj/tomlev/actions/workflows/main.yml)
[![Coverage Status](https://badgen.net/coveralls/c/github/thesimj/tomlev)](https://coveralls.io/github/thesimj/tomlev?branch=main)
![Versions](https://badgen.net/pypi/python/tomlev)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/pypi/l/tomlev.svg)](LICENSE)
[![Downloads](https://static.pepy.tech/personalized-badge/tomlev?period=total&units=international_system&left_color=black&right_color=green&left_text=Downloads)](https://pepy.tech/project/tomlev)

### Motivation

TomlEv is a lightweight Python framework designed to simplify environment variable management using TOML configuration
files. It allows you to:

- Define configuration in structured TOML files
- Reference environment variables in your TOML files
- Provide default values for missing environment variables
- Access configuration using intuitive dot notation or dictionary-like syntax
- Convert values to appropriate types (bool, int, float, str)
- Format strings with variables

### Install

```shell
# pip
pip install tomlev
```

```shell
# poetry
poetry add tomlev
```

### Basic usage

Create a TOML configuration file (e.g., `config.toml`):

```toml
# config.toml
app_name = "My Application"
debug = "${DEBUG|false}"
environment = "${ENV|development}"

[database]
host = "${DB_HOST|localhost}"
port = "${DB_PORT|5432}"
user = "${DB_USER}"
password = "${DB_PASSWORD}"
name = "${DB_NAME|app_db}"

[redis]
host = "${REDIS_HOST|127.0.0.1}"
port = "${REDIS_PORT|6379}"
```

Use TomlEv in your Python code:

```python
from tomlev import TomlEv

# Load configuration from TOML file and environment variables
env = TomlEv("config.toml")

# Access configuration using dot notation
print(f"App: {env.var.app_name}")
print(f"Environment: {env.var.environment}")

# Access nested configuration
db_host = env.var.database.host
db_port = env.var.database.port

# Access using dictionary-like syntax
redis_host = env["redis.host"]
redis_port = env.int("redis.port")  # Convert to integer

# Check if a configuration key exists
if "database.ssl" in env:
    ssl_enabled = env.bool("database.ssl")
```

### Strict mode

By default, TomlEv operates in strict mode, which means it will raise a `ValueError` if:

1. An environment variable referenced in the TOML file is not defined and has no default value
2. The same variable is defined multiple times in the .env file

This helps catch configuration errors early. You can disable strict mode in two ways:

```python
# Method 1: Set the environment variable TOMLEV_STRICT_DISABLE
import os

os.environ["TOMLEV_STRICT_DISABLE"] = "true"
env = TomlEv("config.toml")

# Method 2: Pass strict=False when creating the TomlEv instance
env = TomlEv("config.toml", strict=False)
```

When strict mode is disabled, TomlEv will not raise errors for missing environment variables or duplicate definitions.

### Support

If you like **TomlEv**, please give it a star ⭐ https://github.com/thesimj/tomlev

### License

MIT licensed. See the [LICENSE](LICENSE) file for more details.
