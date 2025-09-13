from __future__ import annotations

import os
import tempfile

import pytest

from tomlev import BaseConfigModel, ConfigValidationError, TomlEv


class Empty(BaseConfigModel):
    pass


def test_invalid_include_type_strict() -> None:
    content = """
[t]
__include = 123
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(content)
        main = f.name

    try:
        with pytest.raises(ConfigValidationError, match="__include must be a string or list of strings"):
            TomlEv(Empty, main, None, strict=True).validate()
    finally:
        os.unlink(main)


def test_missing_include_non_strict() -> None:
    content = """
[t]
__include = "missing.toml"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(content)
        main = f.name

    class Root(BaseConfigModel):
        t: dict

    try:
        # In non-strict mode, missing includes are skipped and __include is removed,
        # leaving an empty table that should validate against a dict field.
        cfg = TomlEv(Root, main, None, strict=False).validate()
        assert cfg.t == {}
    finally:
        os.unlink(main)


def test_include_cycle_strict() -> None:
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.toml")
        b = os.path.join(d, "b.toml")
        with open(a, "w", encoding="utf8") as fa:
            fa.write('[x]\n__include = "b.toml"\n')
        with open(b, "w", encoding="utf8") as fb:
            fb.write('[y]\n__include = "a.toml"\n')

        with pytest.raises(ConfigValidationError, match="Include cycle detected"):
            TomlEv(Empty, a, None, strict=True).validate()


def test_include_cache_and_merge() -> None:
    class Holder(BaseConfigModel):
        a: dict

    with tempfile.TemporaryDirectory() as d:
        main = os.path.join(d, "main.toml")
        inc = os.path.join(d, "inc.toml")
        with open(inc, "w", encoding="utf8") as fi:
            fi.write('[a]\nkey = "val"\n[a.nested]\nflag = true\n')
        with open(main, "w", encoding="utf8") as fm:
            fm.write('__include = ["inc.toml", "inc.toml"]\n')

        cfg = TomlEv(Holder, main, None, strict=True).validate()
        assert cfg.a["key"] == "val"
        assert cfg.a["nested"]["flag"] is True


def test_envfile_line_without_equal_is_skipped() -> None:
    class Single(BaseConfigModel):
        x: str

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as e:
        e.write("LINE_WITHOUT_EQUAL\n")
        e.write("X=ok\n")
        env_path = e.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as t:
        t.write('x = "${X}"\n')
        toml_path = t.name

    try:
        cfg = TomlEv(Single, toml_path, env_path, strict=True).validate()
        assert cfg.x == "ok"
    finally:
        os.unlink(env_path)
        os.unlink(toml_path)
