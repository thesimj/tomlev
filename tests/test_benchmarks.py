"""Performance benchmark tests for TomlEv.

These tests measure the performance characteristics of TomlEv operations
to detect performance regressions and guide optimization efforts.
"""

from __future__ import annotations

import tempfile
from typing import Any

import pytest

from tomlev import BaseConfigModel, TomlEv


class BenchmarkConfig(BaseConfigModel):
    """Configuration model for benchmarking tests."""

    name: str
    port: int
    enabled: bool
    ratio: float
    tags: list[str]
    metadata: dict[str, Any]


class LargeConfig(BaseConfigModel):
    """Large configuration model for stress testing."""

    # Many string fields
    field1: str
    field2: str
    field3: str
    field4: str
    field5: str

    # Numeric fields
    count1: int
    count2: int
    count3: int

    # Boolean fields
    flag1: bool
    flag2: bool
    flag3: bool

    # Collection fields
    tags: list[str]
    numbers: list[int]
    flags: list[bool]

    # Dictionary fields
    config: dict[str, Any]
    data: dict[str, Any]


@pytest.mark.benchmark
class TestConfigCreationBenchmarks:
    """Benchmarks for configuration model creation and validation."""

    def test_simple_config_creation_benchmark(self, benchmark):
        """Benchmark simple configuration model creation."""
        config_data = {
            "name": "test-service",
            "port": 8080,
            "enabled": True,
            "ratio": 0.75,
            "tags": ["web", "api", "prod"],
            "metadata": {"version": "1.0", "build": 123},
        }

        result = benchmark(BenchmarkConfig, **config_data)

        # Verify the result is correct
        assert result.name == "test-service"
        assert result.port == 8080
        assert result.enabled is True

    def test_large_config_creation_benchmark(self, benchmark):
        """Benchmark a large configuration model with many fields."""
        config_data = {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
            "field4": "value4",
            "field5": "value5",
            "count1": 100,
            "count2": 200,
            "count3": 300,
            "flag1": True,
            "flag2": False,
            "flag3": True,
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "flags": [True, False, True, False, True],
            "config": {"key1": "val1", "key2": "val2", "key3": "val3"},
            "data": {"items": [1, 2, 3], "enabled": True, "name": "test"},
        }

        result = benchmark(LargeConfig, **config_data)

        # Verify essential fields
        assert result.field1 == "value1"
        assert result.count1 == 100
        assert len(result.tags) == 5

    def test_type_conversion_benchmark(self, benchmark):
        """Benchmark type conversion performance."""
        config_data = {
            "name": "test",
            "port": "8080",  # String that needs conversion to int
            "enabled": "true",  # String that needs conversion to bool
            "ratio": "0.75",  # String that needs conversion to float
            "tags": ["1", "2", "3"],  # List of strings
            "metadata": {"count": "42", "active": "yes"},  # Dict with mixed types
        }

        class ConversionConfig(BaseConfigModel):
            name: str
            port: int
            enabled: bool
            ratio: float
            tags: list[str]
            metadata: dict[str, Any]

        result = benchmark(ConversionConfig, **config_data)

        # Verify conversions worked
        assert isinstance(result.port, int)
        assert isinstance(result.enabled, bool)
        assert isinstance(result.ratio, float)


@pytest.mark.benchmark
class TestTomlLoadingBenchmarks:
    """Benchmarks for TOML file loading and parsing."""

    def test_small_toml_loading_benchmark(self, benchmark):
        """Benchmark loading a small TOML configuration file."""
        toml_content = """
name = "benchmark-app"
port = 3000
enabled = true
ratio = 0.95
tags = ["benchmark", "test", "performance"]

[metadata]
version = "1.0.0"
build = 42
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            toml_file = f.name

        try:
            result = benchmark(lambda: TomlEv(BenchmarkConfig, toml_file, None).validate())

            # Verify the result
            assert result.name == "benchmark-app"
            assert result.port == 3000

        finally:
            import os

            os.unlink(toml_file)

    def test_large_toml_loading_benchmark(self, benchmark):
        """Benchmark loading a large TOML configuration file."""
        # Generate a large TOML file content
        tags_list = [f'"tag{i}"' for i in range(1, 21)]
        numbers_list = list(range(1, 101))
        flags_list = [str(i % 2 == 0).lower() for i in range(1, 51)]
        config_keys = chr(10).join(f'key{i} = "value{i}"' for i in range(1, 26))
        items_list = list(range(1, 21))

        toml_content = f"""
field1 = "value1"
field2 = "value2"
field3 = "value3"
field4 = "value4"
field5 = "value5"

count1 = 1000
count2 = 2000
count3 = 3000

flag1 = true
flag2 = false
flag3 = true

tags = [{", ".join(tags_list)}]
numbers = [{", ".join(map(str, numbers_list))}]
flags = [{", ".join(flags_list)}]

[config]
{config_keys}

[data]
name = "large-config"
items = [{", ".join(map(str, items_list))}]
enabled = true
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            toml_file = f.name

        try:
            result = benchmark(lambda: TomlEv(LargeConfig, toml_file, None).validate())

            # Verify some key fields
            assert result.field1 == "value1"
            assert result.count1 == 1000
            assert len(result.tags) == 20

        finally:
            import os

            os.unlink(toml_file)

    def test_env_substitution_benchmark(self, benchmark):
        """Benchmark environment variable substitution performance."""
        import os

        # Set up environment variables
        env_vars = {"BENCH_NAME": "env-benchmark", "BENCH_PORT": "9000", "BENCH_DEBUG": "true", "BENCH_RATIO": "0.85"}

        for key, value in env_vars.items():
            os.environ[key] = value

        toml_content = """
name = "${BENCH_NAME|-default-name}"
port = "${BENCH_PORT|-8080}"
enabled = "${BENCH_DEBUG|-false}"
ratio = "${BENCH_RATIO|-0.5}"
tags = ["env", "substitution", "benchmark"]

[metadata]
env = "benchmark"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            toml_file = f.name

        try:
            result = benchmark(lambda: TomlEv(BenchmarkConfig, toml_file, None).validate())

            # Verify environment substitution worked
            assert result.name == "env-benchmark"
            assert result.port == 9000
            assert result.enabled is True

        finally:
            import os

            os.unlink(toml_file)
            # Clean up environment variables
            for key in env_vars:
                os.environ.pop(key, None)


class Level3Config(BaseConfigModel):
    """Deeply nested configuration level 3."""

    value: str
    count: int


class Level2Config(BaseConfigModel):
    """Deeply nested configuration level 2."""

    name: str
    level3: Level3Config


class Level1Config(BaseConfigModel):
    """Deeply nested configuration level 1."""

    enabled: bool
    level2: Level2Config


class RootConfig(BaseConfigModel):
    """Root configuration for deep nesting test."""

    app_name: str
    level1: Level1Config


@pytest.mark.benchmark
@pytest.mark.slow
class TestStressBenchmarks:
    """Stress tests and benchmarks for extreme scenarios."""

    def test_deeply_nested_config_benchmark(self, benchmark):
        """Benchmark deeply nested configuration structures."""

        toml_content = """
app_name = "nested-benchmark"

[level1]
enabled = true

[level1.level2]
name = "deep-config"

[level1.level2.level3]
value = "deeply-nested"
count = 42
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            toml_file = f.name

        try:
            result = benchmark(lambda: TomlEv(RootConfig, toml_file, None).validate())
        finally:
            import os

            os.unlink(toml_file)

        # Verify nested access works
        assert result.app_name == "nested-benchmark"
        assert result.level1.level2.level3.value == "deeply-nested"

    def test_many_list_items_benchmark(self, benchmark):
        """Benchmark configuration with large lists."""

        class ListHeavyConfig(BaseConfigModel):
            strings: list[str]
            numbers: list[int]
            booleans: list[bool]

        config_data = {
            "strings": [f"item-{i}" for i in range(1000)],
            "numbers": list(range(1000)),
            "booleans": [i % 2 == 0 for i in range(1000)],
        }

        result = benchmark(ListHeavyConfig, **config_data)

        # Verify large lists are handled correctly
        assert len(result.strings) == 1000
        assert len(result.numbers) == 1000
        assert len(result.booleans) == 1000
        assert result.strings[999] == "item-999"
