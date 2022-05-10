from __future__ import annotations

from core import colors

import re
import json
import os

class Config:
    def __init__(self, **kwargs) -> None:
        """Instantiate config with default settings"""

        self.stopcode: int = 3522
        self.ignore_headsigns: list[str] = []
        self.departure_count = 10
        self.visible_count: int | None = None
        self.poll_rate: int = 30
        self.endpoint: str = "https://api.digitransit.fi/routing/v1/routers/waltti/index/graphql"
        self.window_size: list[int] = [360, 640]
        self.fullscreen: bool = False
        self.framerate: int = -1
        self.hide_mouse: bool = True
        self.enabled_embeds: list[str] = []

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
            print(f"{colors.ConsoleColors.YELLOW}No config found on path: '{config_path}'\nCreating one with default settings.{colors.ConsoleColors.RESET}")
            _default_config = Config.default
            Config.save(_default_config, config_path)
            return _default_config

        assert isinstance(data, dict)

        conf: Config = Config()
        for k, v in data.items():
            original_value = getattr(conf, k, None)
            if original_value is None:
                print(f"{colors.ConsoleColors.RED}No key '{k}' found to assign value '{v}'{colors.ConsoleColors.RESET}")
                continue
            if not isinstance(v, type(original_value)):
                print(f"{colors.ConsoleColors.RED}Value '{v}' cannot be assigned to key '{k}' with value '{original_value}' and will be skipped.{colors.ConsoleColors.RESET}", True)
                continue

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

            out += f"\n{k}: {type(v).__name__} (Default: {v})"

        return out


current: Config


def init():
    global current
    current = Config.load("./config.json")

def quit():
    Config.save(current, "./config.json")
