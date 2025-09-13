from __future__ import annotations

import io
import json
import os
import tempfile
from contextlib import redirect_stderr, redirect_stdout

from tomlev.__main__ import main as tomlev_main


def test_cli_validate_success_and_errors() -> None:
    # Success case
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "ok"\n')
        ok_toml = f.name

    try:
        code = tomlev_main(["validate", "--toml", ok_toml, "--no-env-file", "--no-environ"])
        assert code == 0
    finally:
        os.unlink(ok_toml)

    # Strict error for missing variable
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f2:
        f2.write('x = "$MISSING"\n')
        bad_toml = f2.name

    try:
        code = tomlev_main(["validate", "--toml", bad_toml, "--no-env-file", "--no-environ", "--strict"])  # noqa: F841
        assert code == 1
        # Non-strict should pass
        code2 = tomlev_main(["validate", "--toml", bad_toml, "--no-env-file", "--no-environ", "--no-strict"])
        assert code2 == 0
    finally:
        os.unlink(bad_toml)


def test_cli_validate_missing_file_and_bad_toml() -> None:
    # Missing file
    code = tomlev_main(["validate", "--toml", "__does_not_exist__.toml", "--no-env-file", "--no-environ"])
    assert code == 1

    # TOML decode error
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('x = "\\q"\n')  # invalid escape in TOML
        path = f.name

    try:
        code2 = tomlev_main(["validate", "--toml", path, "--no-env-file", "--no-environ"])
        assert code2 == 1
    finally:
        os.unlink(path)


def test_cli_render_success() -> None:
    # Test successful rendering
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('name = "test"\nport = "8080"\ndebug = "true"\n')
        toml_file = f.name

    try:
        # Capture stdout to verify JSON output
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            code = tomlev_main(["render", "--toml", toml_file, "--no-env-file", "--no-environ"])

        assert code == 0
        output = captured_output.getvalue().strip()

        # Verify it's valid JSON with correct indentation
        parsed = json.loads(output)
        assert parsed["name"] == "test"
        assert parsed["port"] == "8080"
        assert parsed["debug"] == "true"

        # Verify indentation (should contain newlines and spaces)
        assert "\n" in output
        assert "  " in output  # 2-space indentation
    finally:
        os.unlink(toml_file)


def test_cli_render_error_cases() -> None:
    # Test missing file
    captured_stderr = io.StringIO()
    with redirect_stderr(captured_stderr):
        code = tomlev_main(["render", "--toml", "__does_not_exist__.toml", "--no-env-file", "--no-environ"])
    assert code == 1

    # Test invalid TOML
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('x = "\\q"\n')  # invalid escape in TOML
        invalid_toml = f.name

    try:
        captured_stderr2 = io.StringIO()
        with redirect_stderr(captured_stderr2):
            code2 = tomlev_main(["render", "--toml", invalid_toml, "--no-env-file", "--no-environ"])
        assert code2 == 1
    finally:
        os.unlink(invalid_toml)
