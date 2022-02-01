from datetime import datetime, date
from typing import Dict

from tomli import loads

from tomlev import __version__, TomlEv


def test_it_should_match_module_version():
    with open("pyproject.toml", "r") as fp:
        project: Dict = loads(fp.read())

    # match version inside pyproject and module
    assert __version__ == project["tool"]["poetry"]["version"]


def test_it_should_load_and_parse_pyproject_file():
    env: TomlEv = TomlEv("tests/pyproject.toml", envfile="tests/tests.env", tomlfile="tests/tests.toml")

    assert env.var.debug
    assert env.var.environment == "testing"

    assert env.var.database.host == "127.0.0.1"
    assert env.var.database.user == "db_user"
    assert env.environ["DB_USER"] == "db_user"
    assert env.var.redis.path.device.format(id=100) == "device:100:run"

    assert env.var.extra.tools.verbose
    assert env.var.extra.tools.uri == "http://127.0.0.1/api"
    assert env.var.time == datetime.fromisoformat("2022-01-01T00:00:00+00:00")
    assert env.var.date == date.fromisoformat("2022-01-01")


def test_it_should_work_as_keys():
    env: TomlEv = TomlEv("tests/pyproject.toml", envfile="tests/tests.env", tomlfile="tests/tests.toml")

    assert env["title_toml"] == "title-000-111"
    assert env["extra.tools.uri"] == "http://127.0.0.1/api"

    # format
    assert env.format("redis.path.device", id=100) == "device:100:run"
