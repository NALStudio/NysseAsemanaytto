from __future__ import annotations
from dataclasses import dataclass, field
from types import UnionType
from typing import get_type_hints, get_args

from core import colors
from core import logging

import re
import json
import os


@dataclass
class Config:

    stopcode: int = 3522
    ignore_headsigns: list[str] = field(default_factory=list)
    departure_count: int = 10
    visible_count: int | None = None
    poll_rate: int = 30
    endpoint: str = "https://api.digitransit.fi/routing/v1/routers/waltti/index/graphql"
    window_size: tuple[int, int] = (360, 640) # Value loaded from json is a list
    fullscreen: bool = False
    framerate: int = -1
    hide_mouse: bool = True
    enabled_embeds: list[str] = field(default_factory=list)


    @classmethod
    @property
    def default(cls):
        return cls()

    @staticmethod
    def load(config_path: str) -> Config:
        """Load config with settings from filepath json"""

        def remove_available_comment(content: str) -> str:
            content_parts = content.split("{")
            content_start = re.sub(r"/\*.*?\*/", "", content_parts[0], flags=re.DOTALL)
            content_end = "{" + "{".join(content_parts[1:])
            return content_start + content_end

        data: dict[str, str | int | float | bool]
        if os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                content = remove_available_comment(f.read())
                data = json.loads(content)
        else:
            logging.warning(f"No config found on path: '{config_path}'\nCreating one with default settings.")
            _default_config = Config.default
            Config.save(_default_config, config_path)
            return _default_config

        assert isinstance(data, dict)

        conf: Config = Config()
        for k, v in data.items():
            # Disable all checks until we come up with a better system...
            #
            # original_value = getattr(conf, k, None)
            # if original_value is None:
            #     logging.error(f"No key '{k}' found to assign value '{v}'")
            #     continue
            # if not isinstance(v, type(original_value)):
            #     logging.error(f"Value '{v}' cannot be assigned to key '{k}' with value '{original_value}' and will be skipped")
            #     continue

            setattr(conf, k, v)

        return conf

    @staticmethod
    def save(config: Config, config_path: str) -> None:
        default = Config()

        to_save: dict[str, str | int | float | bool] = {}
        for k, v in config.__dict__.items():
            if k.startswith("_"):
                continue
            if getattr(default, k) == v:  # If value is same as default
                continue

            to_save[k] = v

        with open(config_path, "w", encoding="utf-8") as f:
            json_str = json.dumps(to_save, indent=4)
            available_settings = Config._generate_available_settings()
            f.write(f"/*\n{available_settings}\n*/\n{json_str}")

    @staticmethod
    def _generate_available_settings() -> str:
        out = "Available settings (json):\n"
        for k, v in Config().__dict__.items():
            if k.startswith("_"):
                continue

            typehint: type | UnionType = get_type_hints(Config)[k]
            typename = typehint.__name__ if not isinstance(typehint, UnionType) else str(typehint)
            typeargs: tuple[type, ...] = get_args(typehint) if not isinstance(typehint, UnionType) else tuple()
            if len(typeargs) > 0:
                typeargstrings = [targ.__name__ for targ in typeargs]
                typename += f"<{', '.join(typeargstrings)}>"
            typename = typename.replace("None", "null")
            out += f"\n{k}: {typename} (Default: {json.dumps(v)})"

        return out


current: Config


def init():
    global current
    current = Config.load("./config.json")


def quit():
    Config.save(current, "./config.json")
