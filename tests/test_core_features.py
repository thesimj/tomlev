from __future__ import annotations

import os
import tempfile

from tomlev import BaseConfigModel, TomlEv


def test_raw_and_as_dict_roundtrip() -> None:
    class Simple(BaseConfigModel):
        name: str
        port: int
        debug: bool

    toml_content = """
name = "demo"
port = 8080
debug = true
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        toml_file = f.name

    try:
        env = TomlEv(Simple, toml_file, None)
        raw = env.raw
        model = env.validate()

        assert raw == {"name": "demo", "port": 8080, "debug": True}
        assert model.as_dict() == raw
    finally:
        os.unlink(toml_file)


def test_dollar_escapes_in_toml() -> None:
    class M(BaseConfigModel):
        x: str
        y: str

    toml_content = 'x = "$$abc"\ny = "$1def"\n'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        toml_file = f.name

    try:
        cfg = TomlEv(M, toml_file, None, strict=True).validate()
        assert cfg.x == "$abc"
        assert cfg.y == "1def"
    finally:
        os.unlink(toml_file)
