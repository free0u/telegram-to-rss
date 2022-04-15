import pytest
from telethon.sync import TelegramClient

from telegram_to_rss.config import UrlConfig, Config, TelegramCreds
from telegram_to_rss.telegram.client import get_telegram_client


@pytest.fixture
def mock_config(mocker):
    _config = Config(UrlConfig("rss_path/", None, None), TelegramCreds(1, "api_hash"))
    mock = mocker.patch("telegram_to_rss.telegram.client.config")
    mock.return_value = _config

    return mock


@pytest.fixture
def mock_telethon(mocker):
    def start(self):
        return None

    mock = mocker.patch("telegram_to_rss.telegram.client.TelegramClient.start", start)
    return mock


def test_client(mock_config, mock_telethon):
    client = get_telegram_client()
    assert isinstance(client, TelegramClient)


def test_single_client_creation():
    client = get_telegram_client()
    another_client = get_telegram_client()
    assert id(client) == id(another_client)
