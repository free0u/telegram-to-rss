import json
import os
from dataclasses import dataclass

CONFIG_PATH = "config.json"

_config = None


def config():
    return _config


def init_config():
    global _config
    _config = Config.create_from_file()


@dataclass
class TelegramCreds:
    api_id: int
    api_hash: str


@dataclass
class UrlConfig:
    rss_path: str
    heartbeat_path: str
    heartbeat_auth: str


class Config:
    def __init__(self, urls: UrlConfig, telegram_creds: TelegramCreds):
        self.urls = urls
        self.telegram_creds = telegram_creds

    @staticmethod
    def create_from_file():
        d = Config.read_config()

        config = Config(UrlConfig(**d["urls"]), TelegramCreds(**d["telegram_creds"]))

        return config

    @staticmethod
    def read_config():
        path = os.path.expanduser(CONFIG_PATH)
        with open(path, "r") as f:
            config = json.load(f)
            return config

    def __str__(self):
        return json.dumps(self, default=lambda x: x.__dict__, indent=2, sort_keys=True)


def main():
    config = Config()
    print(str(config))


if __name__ == "__main__":
    main()
