import time

import pytest

from telegram_to_rss.config import Config, UrlConfig
from telegram_to_rss.posts.converter import get_grouped_posts, messages_to_posts
from telegram_to_rss.telegram.channels import ChannelAccessInfo
from tests.helpers.messages_generator import gen_message, timestamp_to_datetime_string


@pytest.fixture
def mock_config(mocker):
    _config = Config(UrlConfig("rss_path/", None, None), None)
    mock = mocker.patch("telegram_to_rss.posts.converter.config")
    mock.return_value = _config
    return mock


def test_ignore_all_first_last_message_single(mock_config):
    # from old to start
    messages = [
        gen_message(1, "ignored", "2021-11-04T00:05:23+00:00"),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 5 * 60),  # now - 5 minutes
        ),
    ]

    messages = list(reversed(messages))
    single_posts = messages_to_posts(ChannelAccessInfo("channel", "hash"), messages)
    posts = get_grouped_posts(single_posts)
    assert len(posts) == 0


def test_ignore_all_first_last_message_many(mock_config):
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

    messages = list(reversed(messages))
    single_posts = messages_to_posts(ChannelAccessInfo("channel", "hash"), messages)
    posts = get_grouped_posts(single_posts)
    assert len(posts) == 0


def test_ignore_not_all_first_last_message_many(mock_config):
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

    messages = list(reversed(messages))

    single_posts = messages_to_posts(ChannelAccessInfo("channel", "hash"), messages)
    posts = get_grouped_posts(single_posts)
    assert len(posts) == 1

    assert posts[0]["text"] == "text"
