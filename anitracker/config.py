import pathlib
from typing import Any

import toml

CONFIG_LOCATION = pathlib.Path("~/.config/anitracker/")
DEFAULT_SETTINGS = {"subtitle": "en", "skip_songs_signs": True}
VALUE_TYPE = Any


class Config:
    """Represents user configurable options"""

    def __init__(self) -> None:
        path = (CONFIG_LOCATION / "config.toml").expanduser()
        self.__directory = path.parent
        self.__path = path

        if not self.__directory.exists():
            self.__directory.mkdir(parents=True)

        try:
            self.__config = toml.load(path)
        except FileNotFoundError:
            self.__config = {}

        if "Default" not in self.__config:
            self.__config["Default"] = DEFAULT_SETTINGS
        if "User" not in self.__config:
            self.__config["User"] = {}

    def __getitem__(self, key: str) -> VALUE_TYPE:
        value = self.get_option(key)
        if value is None:
            value = self.get_option(key, section="Default")

        return value

    def __setitem__(self, key: str, value: VALUE_TYPE):
        self.set_option(key, value)

    def set_option(self, key: str, value: VALUE_TYPE, *, section: str = "User"):
        if section not in self.__config:
            self.__config[section] = {}

        self.__config[section][key] = value

        with open(self.__path.expanduser(), "w+") as f:
            toml.dump(self.__config, f)

    def get_option(self, key: str, *, section: str = "User") -> VALUE_TYPE:
        return self.__config.get(section, {}).get(key)
