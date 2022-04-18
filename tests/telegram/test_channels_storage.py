import json

import pytest
from telethon.tl.types import InputPeerChannel

from telegram_to_rss.config import UrlConfig, Config, TelegramCreds
from telegram_to_rss.telegram.channels import (
    _remove_channel_from_cache_impl,
    _load_channels_info_impl,
    ChannelAccessInfo,
)


@pytest.fixture
def mock_config(mocker):
    _config = Config(UrlConfig("rss_path/", None, None), TelegramCreds(1, "api_hash"))
    mock = mocker.patch("telegram_to_rss.telegram.client.config")
    mock.return_value = _config

    return mock


@pytest.fixture
def mock_telethon(mocker):
    mock = mocker.patch("telegram_to_rss.telegram.channels.get_telegram_client")
    return mock


def write_json_into_test_file(file, data):
    s = json.dumps(data, default=lambda x: x.__dict__, indent=2, sort_keys=True)
    file.write(s)


def read_json_from_test_file(file):
    with open(file, "r") as f:
        print(file)
        return json.load(f)


def test_loading_existed(mock_config, mock_telethon, tmpdir):
    channels_info = tmpdir.join("channels.json")
    channels_request_list = tmpdir.join("channels_request.txt")

    channels_request_list.write("\n".join(["a", "b"]))

    content = {
        "a": {
            "access_hash": 1,
            "channel_id": 2,
        },
        "b": {
            "access_hash": 3,
            "channel_id": 4,
        },
    }

    write_json_into_test_file(channels_info, content)

    channels = _load_channels_info_impl(channels_info, channels_request_list)
    assert len(channels) == 2
    assert (
        ChannelAccessInfo(
            "a",
            InputPeerChannel(content["a"]["channel_id"], content["a"]["access_hash"]),
        )
        in channels
    )
    assert (
        ChannelAccessInfo(
            "b",
            InputPeerChannel(content["b"]["channel_id"], content["b"]["access_hash"]),
        )
        in channels
    )


def test_loading_not_existed(mock_config, mock_telethon, tmpdir):
    test_user_id = 100
    test_access_hash = 200
    mock_telethon.return_value.get_input_entity.return_value = InputPeerChannel(
        test_user_id, test_access_hash
    )

    channels_info = tmpdir.join("channels.json")
    channels_request_list = tmpdir.join("channels_request.txt")

    channels_request_list.write("\n".join(["a"]))

    content = {}

    write_json_into_test_file(channels_info, content)

    channels = _load_channels_info_impl(channels_info, channels_request_list)

    assert mock_telethon.called

    assert channels == [
        ChannelAccessInfo("a", InputPeerChannel(test_user_id, test_access_hash))
    ]

    assert read_json_from_test_file(channels_info) == {
        "a": {
            "access_hash": test_access_hash,
            "channel_id": test_user_id,
        }
    }


def test_remove_not_existed_channel(mock_config, mock_telethon, tmpdir):
    p = tmpdir.join("channels.json")

    content = {
        "a": {
            "access_hash": 1,
            "channel_id": 2,
        },
        "b": {
            "access_hash": 3,
            "channel_id": 4,
        },
    }

    write_json_into_test_file(p, content)

    is_changed = _remove_channel_from_cache_impl(p, "not_existed")
    assert not is_changed

    assert content == read_json_from_test_file(p)


def test_remove_existed_channel(mock_config, mock_telethon, tmpdir):
    p = tmpdir.join("channels.json")

    content = {
        "a": {
            "access_hash": 1,
            "channel_id": 2,
        },
        "b": {
            "access_hash": 3,
            "channel_id": 4,
        },
    }

    write_json_into_test_file(p, content)

    is_changed = _remove_channel_from_cache_impl(p, "b")
    assert is_changed

    assert read_json_from_test_file(p) == {
        "a": {
            "access_hash": 1,
            "channel_id": 2,
        }
    }
