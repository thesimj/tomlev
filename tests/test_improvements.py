from __future__ import annotations

import os
import tempfile
from typing import Literal

from tomlev import BaseConfigModel, TomlEv
from tomlev.__main__ import main as tomlev_main


class UnionOptionalConfig(BaseConfigModel):
    value: int | str
    maybe: int | None


def test_optional_and_union_conversion() -> None:
    cfg = UnionOptionalConfig(value="123", maybe=None)
    assert isinstance(cfg.value, int) and cfg.value == 123
    assert cfg.maybe is None

    cfg2 = UnionOptionalConfig(value="abc", maybe="7")
    assert isinstance(cfg2.value, str) and cfg2.value == "abc"
    assert isinstance(cfg2.maybe, int) and cfg2.maybe == 7


class ChildModel(BaseConfigModel):
    a: int


class ParentModel(BaseConfigModel):
    children: list[ChildModel]
    mapping: dict[str, ChildModel]


def test_nested_model_collections() -> None:
    cfg = ParentModel(children=[{"a": "5"}], mapping={"x": {"a": 6}})
    assert isinstance(cfg.children[0], ChildModel) and cfg.children[0].a == 5
    assert isinstance(cfg.mapping["x"], ChildModel) and cfg.mapping["x"].a == 6


class DefaultsModel(BaseConfigModel):
    flag: bool = True
    count: int = 5


def test_class_defaults_preferred() -> None:
    cfg = DefaultsModel()
    assert cfg.flag is True
    assert cfg.count == 5


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


def test_literal_numeric_and_bool() -> None:
    class L(BaseConfigModel):
        num: Literal[1, 2, 3]
        flt: Literal[2.5, 3.5]
        flag: Literal[True, False]

    cfg = L(num="2", flt="3.5", flag="true")
    assert isinstance(cfg.num, int) and cfg.num == 2
    assert isinstance(cfg.flt, float) and cfg.flt == 3.5
    assert isinstance(cfg.flag, bool) and cfg.flag is True
