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


def test_grouping(mocker, mock_config):
    mock = mocker.patch("telegram_to_rss.main.load_channels_posts")

    # from old to start
    messages = [
        gen_message(1, "ignored 1", "2021-11-04T00:05:23"),
        gen_message(1, "ignored 2", "2021-11-04T00:06:23"),
        gen_message(1, "ignored 3", "2021-11-04T00:07:23"),
        gen_message(1, "text 1", "2021-11-04T01:07:23"),
        gen_message(1, "text 2.1", "2021-11-04T02:07:23"),
        gen_message(1, "text 2.2", "2021-11-04T02:08:23"),
        gen_message(1, "text 2.3", "2021-11-04T02:09:23"),
        gen_message(1, "text 3", "2021-11-04T04:09:23"),
        gen_message(
            2,
            "text 4",
            timestamp_to_datetime_string(time.time() - 19 * 60),  # now - 5 minutes
        ),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 7 * 60),  # now - 5 minutes
        ),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 5 * 60),  # now - 5 minutes
        ),
    ]

    mock.return_value = list(reversed(messages))

    posts = get_grouped_posts_from_channel("channel", "entity_id")
    assert len(posts) == 4

    posts = list(reversed(posts))

    assert posts[0]["text"] == "text 1"

    assert (
        posts[1]["text"]
        == "text 2.1<br/>***********<br/>text 2.2<br/>***********<br/>text 2.3"
    )
    assert posts[2]["text"] == "text 3"

    assert posts[3]["text"] == "text 4"
