import time

import pytest

from telegram_to_rss import main as _main
from telegram_to_rss.config import Config, UrlConfig
from telegram_to_rss.main import get_grouped_posts_from_channel
from tests.helpers.messages_generator import gen_message, timestamp_to_datetime_string


@pytest.fixture
def mock_config(mocker):
    config = Config(UrlConfig("rss_path/", None, None), None)
    mock = mocker.patch.object(_main, "config", config)
    return mock


def test_ignore_all_first_last_message_single(mocker, mock_config):
    mock = mocker.patch("telegram_to_rss.main.load_channels_posts")

    # from old to start
    messages = [
        gen_message(1, "ignored", "2021-11-04T00:05:23+00:00"),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 5 * 60),  # now - 5 minutes
        ),
    ]

    mock.return_value = list(reversed(messages))

    posts = get_grouped_posts_from_channel("channel", "entity_id")
    assert len(posts) == 0


def test_ignore_all_first_last_message_many(mocker, mock_config):
    mock = mocker.patch("telegram_to_rss.main.load_channels_posts")

    # from old to start
    messages = [
        gen_message(1, "ignored start", "2021-11-04T00:05:23+00:00"),
        gen_message(1, "ignored middle", "2021-11-04T00:06:23+00:00"),
        gen_message(1, "ignored end", "2021-11-04T00:07:23+00:00"),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 5 * 60),  # now - 5 minutes
        ),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 3 * 60),  # now - 5 minutes
        ),
    ]

    mock.return_value = list(reversed(messages))
    posts = get_grouped_posts_from_channel("channel", "entity_id")
    assert len(posts) == 0


def test_ignore_not_all_first_last_message_many(mocker, mock_config):
    mock = mocker.patch("telegram_to_rss.main.load_channels_posts")

    # from old to start
    messages = [
        gen_message(1, "ignored start", "2021-11-04T00:05:23+00:00"),
        gen_message(1, "ignored start", "2021-11-04T00:05:23+00:00"),
        gen_message(1, "ignored end", "2021-11-04T00:01:23+00:00"),
        gen_message(4, "text", "2021-11-04T01:01:23+00:00"),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 5 * 60),  # now - 5 minutes
        ),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 3 * 60),  # now - 5 minutes
        ),
    ]

    mock.return_value = list(reversed(messages))

    posts = get_grouped_posts_from_channel("channel", "entity_id")
    assert len(posts) == 1

    assert posts[0]["text"] == "text"
