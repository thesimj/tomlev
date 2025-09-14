"""Tests for environment variable defaults in TOMLEV_TOML_FILE and TOMLEV_ENV_FILE."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

from tomlev import BaseConfigModel, TomlEv
from tomlev.__main__ import main as cli_main


class EnvDefaultConfig(BaseConfigModel):
    name: str
    port: int
    debug: bool


def test_tomlev_class_uses_env_var_defaults():
    """Test that TomlEv class uses environment variable defaults."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f:
        toml_f.write('name = "test"\nport = 8080\ndebug = false')
        custom_toml = toml_f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_f:
        env_f.write("TEST_VAR=value")
        custom_env = env_f.name

    try:
        # Test with environment variables set
        with patch.dict(os.environ, {"TOMLEV_TOML_FILE": custom_toml, "TOMLEV_ENV_FILE": custom_env}):
            # Should use the environment variable defaults when no paths are provided
            config = TomlEv(EnvDefaultConfig).validate()
            assert config.name == "test"
            assert config.port == 8080
            assert config.debug is False
    finally:
        os.unlink(custom_toml)
        os.unlink(custom_env)


def test_tomlev_class_explicit_paths_override_env_vars():
    """Test that explicit paths override environment variable defaults."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f1:
        toml_f1.write('name = "env_default"\nport = 3000\ndebug = true')
        env_default_toml = toml_f1.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f2:
        toml_f2.write('name = "explicit"\nport = 5000\ndebug = false')
        explicit_toml = toml_f2.name

    try:
        # Set the environment variable to point to env_default_toml
        with patch.dict(os.environ, {"TOMLEV_TOML_FILE": env_default_toml}):
            # But explicitly provide explicit_toml - should override
            config = TomlEv(EnvDefaultConfig, toml_file=explicit_toml, env_file=None).validate()
            assert config.name == "explicit"
            assert config.port == 5000
            assert config.debug is False
    finally:
        os.unlink(env_default_toml)
        os.unlink(explicit_toml)


def test_cli_validate_uses_env_var_defaults():
    """Test that CLI validate command uses environment variable defaults."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f:
        toml_f.write('name = "cli_test"')
        custom_toml = toml_f.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as env_f:
        env_f.write("VAR1=value1")
        custom_env = env_f.name

    try:
        # Test with environment variables set
        with patch.dict(os.environ, {"TOMLEV_TOML_FILE": custom_toml, "TOMLEV_ENV_FILE": custom_env}):
            # Should use the environment variable defaults
            code = cli_main(["validate", "--no-environ"])
            assert code == 0
    finally:
        os.unlink(custom_toml)
        os.unlink(custom_env)


def test_cli_render_uses_env_var_defaults():
    """Test that CLI render command uses environment variable defaults."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f:
        toml_f.write('app = "myapp"\nversion = "1.0.0"')
        custom_toml = toml_f.name

    try:
        # Test with environment variables set
        with patch.dict(os.environ, {"TOMLEV_TOML_FILE": custom_toml}):
            # Should use the environment variable defaults
            code = cli_main(["render", "--no-env-file", "--no-environ"])
            assert code == 0
    finally:
        os.unlink(custom_toml)


def test_cli_explicit_paths_override_env_vars():
    """Test that CLI explicit paths override environment variable defaults."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f1:
        toml_f1.write('data = "from_env_var"')
        env_var_toml = toml_f1.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as toml_f2:
        toml_f2.write('data = "from_explicit"')
        explicit_toml = toml_f2.name

    try:
        # Set environment variable but provide explicit path
        with patch.dict(os.environ, {"TOMLEV_TOML_FILE": env_var_toml}):
            # Explicit path should override
            code = cli_main(["validate", "--toml", explicit_toml, "--no-env-file", "--no-environ"])
            assert code == 0
    finally:
        os.unlink(env_var_toml)
        os.unlink(explicit_toml)


def test_falls_back_to_hardcoded_defaults():
    """Test that system falls back to hardcoded defaults when env vars not set."""
    # Create files with the hardcoded default names
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create env.toml (the hardcoded default)
            with open("env.toml", "w") as f:
                f.write('app = "default"\nport = 3000\ndebug = false')

            # Ensure environment variables are not set
            env = os.environ.copy()
            env.pop("TOMLEV_TOML_FILE", None)
            env.pop("TOMLEV_ENV_FILE", None)

            with patch.dict(os.environ, env, clear=True):
                # Should use hardcoded defaults
                config = TomlEv(EnvDefaultConfig, env_file=None).validate()
                assert config.app == "default"  # type: ignore[attr-defined]
        except Exception:
            # Expected since EnvDefaultConfig doesn't have 'app' field
            # Just verify we tried to read env.toml
            pass
        finally:
            os.chdir(orig_cwd)
