from __future__ import annotations

import os
import tempfile

from tomlev import BaseConfigModel, TomlEv


def test_envfile_parsing_features() -> None:
    class E(BaseConfigModel):
        a: str
        b: str
        c: str

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as envf:
        envf.write('export NAME="va#lue"\n')
        envf.write("UNQUOTED=bar # comment here\n")
        envf.write(r"ESCAPED=baz\#hash\n".replace("\\n", ""))
        env_file = envf.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(
            'a = "${NAME}"\n'  # preserves # inside quotes
            'b = "${UNQUOTED}"\n'  # strips inline comment
            'c = "${ESCAPED}"\n'  # keeps escaped hash
        )
        toml_file = f.name

    try:
        cfg = TomlEv(E, toml_file, env_file, strict=True).validate()
        assert cfg.a == "va#lue"
        assert cfg.b == "bar"
        assert cfg.c == r"baz#hash"
    finally:
        os.unlink(env_file)
        os.unlink(toml_file)


def test_envfile_ignored_lines_and_invalid_names() -> None:
    class E(BaseConfigModel):
        v: str

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as envf:
        envf.write("# comment only\n\n")
        envf.write("1BAD=val\n")
        envf.write("OK=ok\n")
        env_file = envf.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('v = "${OK}"\n')
        toml_file = f.name

    try:
        cfg = TomlEv(E, toml_file, env_file, strict=True).validate()
        assert cfg.v == "ok"
    finally:
        os.unlink(env_file)
        os.unlink(toml_file)


def test_envfile_unmatched_quote_is_kept_but_not_used() -> None:
    class E(BaseConfigModel):
        x: str

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as envf:
        envf.write('BAD="oops\n')  # unmatched quote
        env_path = envf.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('x = "ok"\n')
        toml_file = f.name

    try:
        cfg = TomlEv(E, toml_file, env_path, strict=True).validate()
        assert cfg.x == "ok"
    finally:
        os.unlink(env_path)
        os.unlink(toml_file)
