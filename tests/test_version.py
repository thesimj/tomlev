"""Test to ensure __version__ matches version in pyproject.toml"""

import tomllib
from pathlib import Path

import tomlev


def test_version_consistency():
    """Test that __version__ matches the version in pyproject.toml"""
    # Get the path to pyproject.toml (relative to this test file)
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # Read and parse pyproject.toml
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    # Get version from pyproject.toml
    pyproject_version = pyproject_data["project"]["version"]

    # Compare with module's __version__
    assert tomlev.__version__ == pyproject_version, (
        f"Version mismatch: tomlev.__version__ = '{tomlev.__version__}' "
        f"but pyproject.toml version = '{pyproject_version}'"
    )
