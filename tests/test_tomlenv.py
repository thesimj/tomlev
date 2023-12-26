import os
from datetime import datetime, date
from typing import Dict

import pytest
from tomli import loads

from tomlev import __version__, TomlEv


def test_it_should_match_module_version():
    with open("pyproject.toml", "r") as fp:
        project: Dict = loads(fp.read())

    # match version inside pyproject and module
    assert __version__ == project["tool"]["poetry"]["version"]


def test_it_should_load_and_parse_toml_file():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env.var.debug == "true"
    assert env.var.environment == "testing"

    assert env.var.database.host == "127.0.0.1"
    assert env.var.database.user == "db_user"
    assert env.environ["DB_USER"] == "db_user"
    assert env.var.redis.path.device.format(id=100) == "device:100:run"

    assert env.var.extra.tools.verbose
    assert env.var.extra.tools.uri == "http://127.0.0.1/api"
    assert env.var.time == datetime.fromisoformat("2022-01-01T00:00:00+00:00")
    assert env.var.date == date.fromisoformat("2022-01-01")

    assert env.var.demo_database_a.uri == env.var.demo_database_b.uri
    assert env.var.demo_database_a.uri == env.var.demo_database_c.uri

    assert env.var.env_with_ds == "extra_$money_maker"


def test_it_should_work_as_keys():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env["title_toml"] == "title-000-111"
    assert env["extra.tools.uri"] == "http://127.0.0.1/api"

    # format
    assert env.format("redis.path.device", id=100) == "device:100:run"


def test_it_should_work_with_get_funtion():
    env: TomlEv = TomlEv(
        "tests/tests.toml",
        "tests/tests.env",
    )

    assert env.get("title_toml") == "title-000-111"
    assert env.get("extra.tools.uri") == "http://127.0.0.1/api"

    # default value
    assert env.get("not.exists.keys", "not-exist") == "not-exist"
    assert env.get("not.exists.keys") is None

    # format
    assert env.format("redis.path.device", id=100) == "device:100:run"


def test_it_should_work_with_strict_mode_disable():
    with pytest.raises(ValueError) as ex:
        TomlEv(
            "tests/tests_not_exists.toml",
            "tests/tests.env",
        )

    assert str(ex.value) == "$NOT_EXISTS are not defined!"


def test_it_should_be_loaded_with_none_env_file():
    assert TomlEv("tests/tests.toml", None, strict=False)


def test_it_should_start_with_env_not_found_file():
    assert TomlEv("tests/tests.toml", ".not-found.env", strict=False)


def test_it_should_raise_exception_with_toml_not_found_file():
    with pytest.raises(FileNotFoundError) as ex:
        assert TomlEv("not-found.toml", ".not-found.env")

    assert str(ex.value) == "[Errno 2] No such file or directory: 'not-found.toml'"


def test_it_should_get_proper_bool_values():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    # get keys
    true_keys = [k for k in env.keys if "extra.bool.bool_t" in k]
    false_keys = [k for k in env.keys if "extra.bool.bool_f" in k]

    for key in true_keys:
        assert env.bool(key) is True and isinstance(env.bool(key), bool)

    for key in false_keys:
        assert env.bool(key) is False and isinstance(env.bool(key), bool)

    # test default value
    assert env.bool("not.exists.keys", True) is True
    assert env.bool("not.exists.keys", False) is False
    assert env.bool("not.exists.keys") is None


def test_it_should_get_proper_int_values():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env.int("extra.int.int_1") == 1 and isinstance(
        env.int("extra.int.int_1"), int
    )
    assert env.int("extra.int.int_2") == 2 and isinstance(
        env.int("extra.int.int_2"), int
    )
    assert env.int("extra.int.int_3") == 3 and isinstance(
        env.int("extra.int.int_3"), int
    )

    assert env.int("extra.int.not_int") is None


# test float values
def test_it_should_get_proper_float_values():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env.float("extra.float.float_1") == 0.0 and isinstance(
        env.float("extra.float.float_1"), float
    )
    assert env.float("extra.float.float_2") == 1.0 and isinstance(
        env.float("extra.float.float_2"), float
    )
    assert env.float("extra.float.float_3") == 2.2 and isinstance(
        env.float("extra.float.float_3"), float
    )
    assert env.float("extra.float.float_4") == 3.1415 and isinstance(
        env.float("extra.float.float_4"), float
    )

    assert env.float("extra.float.not_float") is None


# test str values
def test_it_should_get_proper_str_values():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env.str("extra.str.str_1") == "0" and isinstance(
        env.str("extra.str.str_1"), str
    )
    assert env.str("extra.str.str_2") == "1.0" and isinstance(
        env.str("extra.str.str_2"), str
    )
    assert env.str("extra.str.str_3") == "2.2" and isinstance(
        env.str("extra.str.str_3"), str
    )
    assert env.str("extra.str.str_4") == "3.1415" and isinstance(
        env.str("extra.str.str_4"), str
    )
    assert env.str("extra.str.str_5") == "true" and isinstance(
        env.str("extra.str.str_5"), str
    )
    assert env.str("extra.str.str_6") == "false" and isinstance(
        env.str("extra.str.str_6"), str
    )
    assert env.str("extra.str.str_7") == "" and isinstance(
        env.str("extra.str.str_7"), str
    )
    assert env.str("extra.str.str_8") == "testing" and isinstance(
        env.str("extra.str.str_8"), str
    )

    assert env.str("extra.str.not_str") is None


# test env values
def test_it_should_get_proper_env_values():
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    # use get function
    assert env.get("DEBUG") == "true"
    assert env.get("DB_DEMO_PORT") == "6969"

    # use typ specific function
    assert env.bool("DEBUG") is True and isinstance(env.bool("DEBUG"), bool)

    assert env.str("DB_DEMO_HOST") == "127.0.0.1"
    assert env.int("DB_DEMO_PORT") == 6969
    assert env.str("DB_DEMO_NAME") == "db_name_demo"
    assert env.str("DB_DEMO_PASS") == "db_pass_demo"

    assert env.str("DB_DEMO_NOT_SET") == ""


def test_it_should_properly_disable_strict_on_env():
    os.environ["TOMLEV_STRICT_DISABLE"] = "true"
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env.strict is False


def test_it_should_properly_disable_strict_on_class():
    os.environ.pop("TOMLEV_STRICT_DISABLE", None)
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env", strict=False)

    assert env.strict is False


def test_it_should_properly_enable_strict_on():
    os.environ.pop("TOMLEV_STRICT_DISABLE", None)
    env: TomlEv = TomlEv("tests/tests.toml", "tests/tests.env")

    assert env.strict is True
