from __future__ import annotations

from typing import Literal

from tomlev import BaseConfigModel


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


def test_literal_numeric_and_bool() -> None:
    class L(BaseConfigModel):
        num: Literal[1, 2, 3]
        flt: Literal[2.5, 3.5]
        flag: Literal[True, False]

    cfg = L(num="2", flt="3.5", flag="true")
    assert isinstance(cfg.num, int) and cfg.num == 2
    assert isinstance(cfg.flt, float) and cfg.flt == 3.5
    assert isinstance(cfg.flag, bool) and cfg.flag is True
