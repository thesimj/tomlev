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
