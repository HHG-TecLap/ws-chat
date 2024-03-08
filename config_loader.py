from typing import TypedDict
import tomllib

from utils import relative_to_file

class _WebConfig(TypedDict):
    app_title: str
    remote_files_loc: str

class Config(TypedDict):
    web: _WebConfig


def read_config() -> Config:
    with open(relative_to_file("config.cfg"), "br") as _config_file:
        config = tomllib.load(_config_file)
    return config # type: ignore