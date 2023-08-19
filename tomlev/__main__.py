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
import io
import re
from os import environ
from os.path import expandvars
from typing import Dict, Any, List, NamedTuple, Set, Optional

try:
    from tomli import loads as tomli_loads
except ImportError:
    tomli_loads = None

__version__ = "0.1.0"

# pattern to remove comments
RE_COMMENTS = re.compile(r"(^#.*\n)", re.MULTILINE | re.UNICODE | re.IGNORECASE)

# pattern to read .env file
RE_DOT_ENV = re.compile(
    r"^(?!\d+)(?P<name>[\w\-\.]+)\=[\"\']?(?P<value>(.*?))[\"\']?$",
    re.MULTILINE | re.UNICODE | re.IGNORECASE,
)

# pattern to extract env variables
RE_PATTERN = re.compile(
    r"(?P<pref>[\"\'])?"
    r"(\$(?:(?P<escaped>(\$|\d+))|"
    r"{(?P<braced>(.*?))(\|(?P<braced_default>.*?))?}|"
    r"(?P<named>[\w\-\.]+)(\|(?P<named_default>.*))?))"
    r"(?P<post>[\"\'])?",
    re.MULTILINE | re.UNICODE | re.IGNORECASE | re.VERBOSE,
)


class TomlEv:
    TOMLEV_STRICT_DISABLE: str = "ENVYAML_STRICT_DISABLE"
    DEFAULT_ENV_TOML_FILE: str = "env.toml"
    DEFAULT_ENV_FILE: str = ".env"

    # variables
    __vars: Dict = None
    __strict: bool = True

    def __init__(
        self,
        toml_file: Optional[str] = DEFAULT_ENV_TOML_FILE,
        env_file: Optional[str] = DEFAULT_ENV_FILE,
        strict: bool = True,
        include_environment: bool = True,
    ):
        if tomli_loads is None:
            raise ModuleNotFoundError(
                'TomlEv require "tomli >= 2" module to work. Consider install this module into environment!'
            )

        # read environment
        self.__vars: Dict = dict(environ) if include_environment else {}

        # set strict mode to false if "TOMLEV_STRICT_DISABLE" presents in env else use "strict" from function
        self.__strict = environ.get("TOMLEV_STRICT_DISABLE", strict)

        # read .env files and update environment variables
        self.__dotenv: Dict = self.__read_envfile(env_file, self.__strict)

        # set environ with dot env variables
        self.__vars.update(self.__dotenv)

        # read toml files
        self.__toml_vars = self.__read_toml(toml_file, self.__vars, self.__strict)

        # build named NamedTuple
        self.var: NamedTuple = self.__flat_environment(self.__toml_vars)

        # build keys
        self.keys: Dict[str, Any] = self.__flat_keys(self.__toml_vars)

    @staticmethod
    def __read_envfile(file_path: Optional[str], strict: bool = True) -> Dict:
        config: Dict = {}
        defined: Set[str] = set()

        if file_path:
            with io.open(file_path, mode="rt", encoding="utf8") as fp:
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
    def __read_toml(file_path: str, env: Dict, strict: bool, separator="|") -> Dict:
        # read file
        if file_path:
            with io.open(file_path, mode="rt", encoding="utf8") as fp:
                content: str = fp.read()

            # remove all comments
            content = RE_COMMENTS.sub("", content)

            # not found variables
            not_found_variables = set()

            # changes dictionary
            replaces = dict()

            shifting = 0

            # iterate over findings
            for entry in RE_PATTERN.finditer(content):
                groups = entry.groupdict()  # type: dict

                # replace
                variable = None
                default = None
                replace = None

                if groups["named"]:
                    variable = groups["named"]
                    default = groups["named_default"]

                elif groups["braced"]:
                    variable = groups["braced"]
                    default = groups["braced_default"]

                elif groups["escaped"] and "$" in groups["escaped"]:
                    span = entry.span()
                    content = content[: span[0] + shifting] + groups["escaped"] + content[span[1] + shifting :]
                    # Added shifting since every time we update content we are
                    # changing the original groups spans
                    shifting += len(groups["escaped"]) - (span[1] - span[0])

                if variable is not None:
                    if variable in env:
                        replace = env[variable]
                    elif variable not in env and default is not None:
                        replace = default
                    else:
                        not_found_variables.add(variable)

                if replace is not None:
                    # build match
                    search = "${" if groups["braced"] else "$"
                    search += variable
                    search += separator + default if default is not None else ""
                    search += "}" if groups["braced"] else ""

                    # store findings
                    replaces[search] = replace

            # strict mode
            if strict and not_found_variables:
                raise ValueError(
                    "Strict mode enabled, variables , ".join(["$" + v for v in not_found_variables])
                    + " are not defined!"
                )

            # replace finding with their respective values
            for replace in sorted(replaces, reverse=True):
                content = content.replace(replace, replaces[replace])

            # load proper content
            toml = tomli_loads(content)

            # if contains something
            if toml and isinstance(toml, (dict, list)):
                return toml

        return {}

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

    @property
    def environ(self) -> Dict:
        """Get environments mapping object including .env variables

        :return: A mapping object representing the string environment
        """
        return self.__vars

    def format(self, key: str, **kwargs) -> str:
        """Apply quick format for string values with {arg}

        :param str key: key to argument
        :return: str
        """
        return self.keys[key].format(**kwargs)

    def get(self, key: str, default: Any = None):
        """Get configuration variable with default value. If no `default` value set use None

        :param any key: name for the configuration key
        :param any default: default value if no key found
        :return: any
        """

        return self.keys.get(key, default)

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
