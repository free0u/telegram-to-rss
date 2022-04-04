import time

import pytest

from telegram_to_rss import main as _main
from telegram_to_rss.config import Config, UrlConfig
from telegram_to_rss.main import get_grouped_posts_from_channel
from tests.helpers.messages_generator import *


@pytest.fixture
def mock_config(mocker):
    config = Config(UrlConfig("rss_path/", None, None), None)
    mock = mocker.patch.object(_main, "config", config)
    return mock


@pytest.fixture
def mock_load_channels_posts(mocker):
    mock = mocker.patch("telegram_to_rss.main.load_channels_posts")

    # from old to start
    messages = [
        gen_message(1, "ignored start", "2021-11-04T00:05:23+00:00"),
        gen_message(1, "ignored end", "2021-11-04T00:05:23+00:00"),
        gen_message(2, "text post start", "2021-11-05T00:05:23+00:00"),
        gen_message(3, "text post end", "2021-11-05T00:07:23+00:00"),
        gen_message(
            3,
            "photo post start single",
            "2021-11-11T00:07:23+00:00",
            gen_message_media_photo(111),
        ),
        gen_message(
            2,
            "webpage post single",
            "2021-12-05T00:05:23+00:00",
            gen_message_media_web_page(4, "web title", "web descr"),
        ),
        gen_message(
            2,
            "media document post single",
            "2021-12-06T00:05:23+00:00",
            gen_message_media_document(),
        ),
        gen_message(
            2,
            "text post with ad single #нативнаяинтеграция",
            "2021-12-07T00:05:23+00:00",
        ),
        gen_message(  # should be ignored because too fresh datetime
            2,
            "text post ignored",
            timestamp_to_datetime_string(time.time() - 5 * 60),  # now - 5 minutes
        ),
    ]

    mock.return_value = list(reversed(messages))
    return mock


def test_conversion(mock_load_channels_posts, mock_config):
    posts = get_grouped_posts_from_channel("channel", "entity_id")
    assert len(posts) == 5

    posts = list(reversed(posts))
    text_post_from_two_messages = posts[0]
    post_with_image = posts[1]
    post_with_webpage = posts[2]
    post_with_document = posts[3]
    post_with_ad = posts[4]

    assert (
        text_post_from_two_messages["text"]
        == "text post start<br/>***********<br/>text post end"
    )

    assert (
        post_with_image["text"]
        == '<img src="rss_path/images/channel/111.jpg" width="800"><br/>photo post start single'
    )

    assert (
        post_with_webpage["text"]
        == "webpage post single<br/>-------------------<br/>web title<br/>web descr<br/>"
        + '<img src="rss_path/images/channel/4.jpg" width="400"><br/>-------------------<br/>'
    )

    assert (
        post_with_document["text"]
        == "📦 MessageMediaDocument<br/>media document post single"
    )

    assert (
        post_with_ad["text"] == "text post with ad single #нативнаяинтеграция"
        and post_with_ad["title"]
        == "РЕКЛАМА text post with ad single #нативнаяинтеграция"
    )
