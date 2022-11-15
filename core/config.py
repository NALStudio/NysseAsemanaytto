from __future__ import annotations
from dataclasses import dataclass, field
from types import UnionType
from typing import Annotated, Any, Generic, NamedTuple, TypeVar, get_args, get_type_hints

from core import logging

import re
import json
import os

RequiredT = TypeVar('RequiredT', bound=object)
class Required(NamedTuple, Generic[RequiredT]):
    value: RequiredT | None
NotDefined = Required(None)

@dataclass
class Config:

    stopcode: int = 3522
    """A number (i.e. `3522`). If stopcode includes any leading zeros, strip them (i.e. `0825` => `825`)."""

    departure_count: int = 10
    """A number that determines how many departures to fetch."""

    omit_non_pickups: bool = True
    """Only show departures where boarding is allowed."""

    omit_canceled: bool = False
    """Hide canceled departures."""

    poll_rate: int = 30
    """How often to refresh the departure data. Waits the specified amount of seconds between requests. (If you are not self-hosting the server, you should avoid doing more than 10 requests per second to reduce load on Digitransit's servers.)"""

    endpoint: str = "https://api.digitransit.fi/routing/v1/routers/waltti/index/graphql"
    """The Digitransit API endpoint you want to send requests to. Can be targeted to a server hosted locally."""

    window_size: tuple[int, int] = (360, 640) # Value loaded from json is a list
    """The size of the window"""

    fullscreen: bool = False
    """Fullscreen? (fullscreen resolution is defined by `window_size`)"""

    framerate: int = -1
    """Limit the window refresh rate. (`-1` to disable limit)"""

    hide_mouse: bool = True
    """Hide mouse when over window."""

    enabled_embeds: list[str] = field(default_factory=list)
    """A janky way to enable embeds. Will be improved upon later... At least I hope so."""

    nysse_api_client_id: str | None = None
    """Nysse API client id to enable advanced features. Instructions: http://dev.publictransport.tampere.fi/getting-started"""

    nysse_api_client_secret: str | None = None
    """Nysse API client secret to enable advanced features. Instructions: http://dev.publictransport.tampere.fi/getting-started"""

    # client_id: Required[str] = NotDefined
    # client_secret: Required[str] = NotDefined


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

        to_save: dict[str, str | int | float | bool | None] = {}
        for k in default.__dict__.keys():
            if k.startswith("_"):
                continue
            default_value: Any = getattr(default, k)
            current_value: Any = getattr(config, k)
            if default_value == current_value and default_value is not NotDefined:  # If value is same as default
                continue
            selected_save: str | int | float | bool | None = current_value if default_value is not NotDefined else None

            to_save[k] = selected_save

        with open(config_path, "w", encoding="utf-8") as f:
            json_str = json.dumps(to_save, indent=4)
            available_settings = Config._generate_available_settings()
            f.write(f"/*\n{available_settings}\n*/\n{json_str}")

    @staticmethod
    def _generate_available_settings() -> str:
        out = "Available settings (json):\n"
        default_instance: Config = Config()
        for k, v in default_instance.__dict__.items():
            if k.startswith("_"):
                continue

            typehint: type | UnionType = get_type_hints(Config, include_extras=True)[k]
            typename = typehint.__name__ if not isinstance(typehint, UnionType) else str(typehint)
            typeargs: tuple[type, ...] = get_args(typehint) if not isinstance(typehint, UnionType) else tuple()
            if len(typeargs) > 0:
                typeargstrings = [targ.__name__ for targ in typeargs if not isinstance(targ, Required)]
                typename += f"<{', '.join(typeargstrings)}>"
            typename = typename.replace("None", "null").replace("core.config.Required", "REQUIRED")
            default: str | None = json.dumps(v) if v is not NotDefined else None
            out += f"\n{k}: {typename}"
            if default is not None:
                out += f" (Default: {default})"

        return out


current: Config


def init():
    global current
    current = Config.load("./config.json")


def quit():
    Config.save(current, "./config.json")
