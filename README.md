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
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/pypi/l/tomlev.svg)](LICENSE)
[![Downloads](https://static.pepy.tech/personalized-badge/tomlev?period=total&units=international_system&left_color=black&right_color=green&left_text=Downloads)](https://pepy.tech/project/tomlev)

### Motivation

TomlEv is a lightweight Python framework designed to simplify environment variable management using TOML configuration
files with type-safe configuration models. It allows you to:

- **Type-safe configuration**: Define configuration schemas using Python classes with type hints
- **Automatic type conversion**: Convert environment variables to appropriate types (bool, int, float, str, lists,
  dicts)
- **Nested configuration**: Support for complex nested configuration structures
- **Environment variable substitution**: Reference environment variables in TOML files with `${VAR|-default}` syntax
- **Validation**: Automatic validation of configuration structure and types
- **AI coding agent ready**: Full type checking support makes configurations perfectly compatible with AI coding agents
  and IDEs
- **IDE support**: Complete IDE autocompletion and static type analysis support

### Install

```shell
# pip
pip install tomlev
```

```shell
# uv
uv add tomlev
```

```shell
# poetry
poetry add tomlev
```

### Basic usage

#### 1. Create a TOML configuration file

Create a TOML configuration file (`env.toml` by default):

```toml
# env.toml
app_name = "My Application"
debug = "${DEBUG|-false}"
environment = "${ENV|-development}"

[database]
host = "${DB_HOST|-localhost}"
port = "${DB_PORT|-5432}"
user = "${DB_USER}"
password = "${DB_PASSWORD}"
name = "${DB_NAME|-app_db}"

[redis]
host = "${REDIS_HOST|-127.0.0.1}"
port = "${REDIS_PORT|-6379}"
```

Optionally include fragments inside a table using `__include` (paths are resolved relative to the TOML file):

```toml
# main.toml
[features]
__include = ["features.toml"]
```

```toml
# features.toml (merged under [features])
enabled = true
name = "awesome"
```

#### 2. Define Configuration Models

Create configuration model classes that inherit from `BaseConfigModel`:

```python
from tomlev import BaseConfigModel, TomlEv


class DatabaseConfig(BaseConfigModel):
    host: str
    port: int
    user: str
    password: str
    name: str


class RedisConfig(BaseConfigModel):
    host: str
    port: int


class FeaturesConfig(BaseConfigModel):
    # Matches the content merged under [features] via __include
    enabled: bool
    name: str


class AppConfig(BaseConfigModel):
    app_name: str
    debug: bool
    environment: str

    database: DatabaseConfig
    redis: RedisConfig
    features: FeaturesConfig
```

Tip: See the [File Includes](#file-includes) section for more details on `__include` usage and merge rules.

#### 3. Use TomlEv in your Python code

```python
from tomlev import TomlEv

# Load and validate configuration (using defaults: "env.toml" and ".env")
config: AppConfig = TomlEv(AppConfig).validate()

# Or explicitly specify files (same as defaults)
config: AppConfig = TomlEv(AppConfig, "env.toml", ".env").validate()

# Access configuration with type safety
print(f"App: {config.app_name}")
print(f"Environment: {config.environment}")
print(f"Debug mode: {config.debug}")  # Automatically converted to bool

# Access nested configuration
db_host = config.database.host
db_port = config.database.port  # Automatically converted to int

# All properties are type-safe and validated
redis_host = config.redis.host
redis_port = config.redis.port  # Automatically converted to int
```

### Configuration Models

TomlEv uses `BaseConfigModel` to provide type-safe configuration handling. Here are the supported types:

#### Supported Types

- **Basic types**: `str`, `int`, `float`, `bool`
- **Collections**: `list[T]`, `dict[str, T]` where T is any supported type
- **Complex collections**: `list[dict[str, Any]]` for lists of dictionaries
- **Nested models**: Other `BaseConfigModel` subclasses
- **Generic types**: `typing.Any` for flexible values

#### Advanced Example

```python
from typing import Any
from tomlev import BaseConfigModel, TomlEv


class QueryConfig(BaseConfigModel):
    get_version: str
    get_users: str


class DatabaseConfig(BaseConfigModel):
    host: str
    port: int
    user: str
    password: str
    name: str
    uri: str
    queries: dict[str, str]  # Dictionary of queries


class RedisConfig(BaseConfigModel):
    host: str
    port: int
    keys: list[str]  # List of strings
    nums: list[int]  # List of integers
    atts: list[dict[str, Any]]  # List of dictionaries
    weight: int
    mass: float


class AppConfig(BaseConfigModel):
    debug: bool
    environment: str
    temp: float

    database: DatabaseConfig
    redis: RedisConfig


# Usage with .env file support (uses defaults: "env.toml" and ".env")
config: AppConfig = TomlEv(
    AppConfig,
    "env.toml",  # Default TOML file
    ".env"  # Default .env file
).validate()

# Or simply use defaults
config: AppConfig = TomlEv(AppConfig).validate()
```

### CLI Usage

TomlEv also provides a small CLI to validate TOML configuration files with environment substitution, without writing Python code.

Validate using defaults (`env.toml` and `.env` in the current directory):

```shell
tomlev validate
```

Validate explicit files:

```shell
tomlev validate --toml path/to/app.toml --env-file path/to/.env
```

Disable strict mode (missing variables do not fail):

```shell
tomlev validate --no-strict
```

Ignore the `.env` file or system environment variables:

```shell
tomlev validate --no-env-file         # do not read .env
tomlev validate --no-environ          # do not include process environment
```

Customize the default separator used in `${VAR|-default}` patterns (default is `|-`):

```shell
tomlev validate --separator "|-"
```

Exit codes: returns `0` on success, `1` on validation error (including missing files, substitution errors, or TOML parse errors). This makes it convenient to integrate into CI.

### File Includes

TomlEv supports a simple include mechanism to compose configs from smaller TOML fragments. Place a reserved key `__include` inside any table to include one or more TOML files into that table.

Basic syntax (paths are resolved relative to the referencing file):

```toml
# main.toml
[database]
__include = ["database.toml"]
```

Included file content is merged under the table where `__include` appears. For example:

```toml
# database.toml
host = "${DB_HOST|-localhost}"
port = "${DB_PORT|-5432}"

[nested]
flag = true
```

After expansion and substitution, the effective configuration is equivalent to:

```toml
[database]
host = "localhost"
port = 5432

[database.nested]
flag = true
```

Notes:
- `__include` can be a string or a list of strings: `__include = "file.toml"` or `__include = ["a.toml", "b.toml"]`.
- Includes are expanded using the same environment mapping and strict mode as the parent file.
- Merge rules: dictionaries are deep-merged; non-dicts (strings, numbers, booleans, lists) are replaced by later includes (last one wins).
- Strict mode: missing files and include cycles raise errors. In non-strict mode, they are skipped.
- The `__include` key is removed from the final configuration prior to model validation.

#### TOML File with Complex Types

```toml
debug = "${DEBUG|-false}"
environment = "${CI_ENVIRONMENT_SLUG|-develop}"
temp = "${TEMP_VAL|--20.5}"

[database]
host = "${DB_HOST|-localhost}"
port = "${DB_PORT|-5432}"
user = "${DB_USER}"
password = "${DB_PASSWORD}"
name = "${DB_NAME|-app_db}"
uri = "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST|-localhost}:${DB_PORT|-5432}/${DB_NAME|-app_db}"

[database.queries]
get_version = """SELECT version();"""
get_users = """SELECT * FROM "users";"""

[redis]
host = "${REDIS_HOST|-127.0.0.1}"
port = "${REDIS_PORT|-6379}"
keys = ["one", "two", "three"]
nums = [10, 12, 99]
atts = [{ name = "one", age = 10 }, { name = "two", age = 12 }]
weight = 0.98
mass = 0.78
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
config = TomlEv(AppConfig).validate()  # Uses defaults: "env.toml" and ".env"

# Method 2: Pass strict=False when creating the TomlEv instance
config = TomlEv(AppConfig, strict=False).validate()  # Uses defaults with strict=False
```

When strict mode is disabled, TomlEv will not raise errors for missing environment variables or duplicate definitions.

### Support

If you like **TomlEv**, please give it a star ⭐ https://github.com/thesimj/tomlev

### License

MIT licensed. See the [LICENSE](LICENSE) file for more details.
