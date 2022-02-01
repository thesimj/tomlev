"""
MIT License

Copyright (c) 2022 Mykola Bubelich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import re
from os import environ
from os.path import expandvars
from pathlib import Path
from typing import Dict, Any, List, NamedTuple, Set, Optional

try:
    from tomli import loads as tomli_loads
except ImportError:
    tomli_loads = None

__version__ = "0.0.3"

# pattern to read .env file
RE_DOT_ENV = re.compile(
    r"^(?!\d+)(?P<name>[\w\-\.]+)\=[\"\']?(?P<value>(.*?))[\"\']?$",
    re.MULTILINE | re.UNICODE | re.IGNORECASE,
)


class TomlEv:
    def __init__(
        self,
        pyproject: str = "pyproject.toml",
        envfile: str = ".env",
        tomlfile: str = None,
        strict: bool = True,
        include_environment: bool = True,
    ):
        if tomli_loads is None:
            raise ModuleNotFoundError(
                'TomlEv require "tomli >= 2" module to work. Consider install this module into environment!'
            )

        # read .env files and update environment variables
        self.dotenv: Dict = self.__read_envfile(envfile)

        # set environ with dot env variables
        environ.update(self.dotenv)

        # read environment
        self.environ: Dict = dict(environ) if include_environment else {}

        # read pyproject and toml file
        self.variables: Dict = {**self.__read_pyproject(pyproject), **self.__read_toml(tomlfile)}

        # build named NamedTuple
        self.var: NamedTuple = self.__flat_environment(self.variables)

        # build keys
        self.keys: Dict[str, Any] = {**self.environ, **self.__flat_keys(self.variables)}

    @staticmethod
    def __read_envfile(file_path: Optional[str], strict: bool = True) -> Dict:
        config: Dict = {}
        defined: Set[str] = set()

        if file_path and Path(file_path).exists():
            with Path(file_path).open() as fp:
                content: str = expandvars(fp.read())

            # iterate over findings
            for entry in RE_DOT_ENV.finditer(content):
                name = entry.group("name")
                value = entry.group("value")

                # check double definition
                if name in config:
                    defined.add(name)

                # set config
                config[name] = value

                # strict mode
        if strict and defined:
            raise ValueError(
                "Strict mode enabled, variables " + ", ".join(["$" + v for v in defined]) + " defined several times!"
            )

        return config

    @staticmethod
    def __read_toml(file_path: Optional[str]) -> Dict:
        config: Dict = {}

        if file_path and Path(file_path).exists():
            with Path(file_path).open("r") as fp:
                config: Dict = tomli_loads(expandvars(fp.read()))

        return config

    @staticmethod
    def __read_pyproject(file_path: Optional[str]) -> Dict:
        # read config file
        config: Dict = TomlEv.__read_toml(file_path)

        # return tool tomlev section
        return config["tool"]["tomlev"] if "tool" in config and "tomlev" in config["tool"] else {}

    @staticmethod
    def __flat_environment(env: Dict) -> NamedTuple:
        keys: List[(str, Any)] = []
        values: List[Any] = []

        for key, value in env.items():
            if isinstance(value, dict):
                keys.append((key, "NamedTuple"))
                values.append(TomlEv.__flat_environment(value))
            else:
                keys.append((key, type(value)))
                values.append(value)

        return NamedTuple("NamedTuple", [*keys])(*values)

    @staticmethod
    def __flat_keys(env: Dict, root: str = "") -> Dict:
        config: Dict = {}

        for key, value in env.items():
            if isinstance(value, dict):
                config.update(TomlEv.__flat_keys(value, root=f"{root}{key}."))
            else:
                config[f"{root}{key}"] = value

        return config

    def format(self, key: str, **kwargs) -> str:
        """Apply quick format for string values with {arg}

        :param str key: key to argument
        :return: str
        """
        return self.keys[key].format(**kwargs)

    def __contains__(self, item: str) -> bool:
        """Check if key in configuration

        :param str item: get item
        :return: bool
        """
        return item in self.keys

    def __getitem__(self, key: str) -> Any:
        """Get item ['item']

        :param str key: get environment name as item
        :return: any
        """

        return self.keys[key]
