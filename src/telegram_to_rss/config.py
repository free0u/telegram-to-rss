import json
import os
from dataclasses import dataclass

CONFIG_PATH = "config.json"


class Config:
    def __init__(self):
        d = self.read_config()

        self.telegram_creds = TelegramCreds(**d["telegram_creds"])
        self.urls = UrlConfig(**d["urls"])

    @staticmethod
    def read_config():
        path = os.path.expanduser(CONFIG_PATH)
        with open(path, "r") as f:
            config = json.load(f)
            return config

    def __str__(self):
        return json.dumps(self, default=lambda x: x.__dict__, indent=2, sort_keys=True)


@dataclass
class TelegramCreds:
    api_id: int
    api_hash: str


@dataclass
class UrlConfig:
    rss_path: str
    heartbeat_path: str
    heartbeat_auth: str


def main():
    config = Config()
    print(str(config))


if __name__ == "__main__":
    main()
