import time

import pytest

from telegram_to_rss.config import Config, UrlConfig
from telegram_to_rss.posts.converter import get_grouped_posts, messages_to_posts
from telegram_to_rss.telegram.channels import ChannelAccessInfo
from tests.helpers.messages_generator import (
    gen_message,
    gen_message_media_photo,
    gen_message_media_web_page,
    gen_message_media_document,
    timestamp_to_datetime_string,
)


@pytest.fixture
def mock_config(mocker):
    _config = Config(UrlConfig("rss_path/", None, None), None)
    # mock = mocker.patch.object(
    #     telegram_to_rss.posts.converter, "config", _config
    # )
    mock = mocker.patch("telegram_to_rss.posts.converter.config")
    mock.return_value = _config

    return mock


def mess():
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
    return list(reversed(messages))


def test_conversion(mock_config):
    single_posts = messages_to_posts(ChannelAccessInfo("channel", "hash"), mess())
    posts = get_grouped_posts(single_posts)
    assert len(posts) == 5

    posts = list(reversed(posts))
    text_post_from_two_messages = posts[0]
    post_with_image = posts[1]
    post_with_webpage = posts[2]
    post_with_document = posts[3]
    post_with_ad = posts[4]

    assert (
        text_post_from_two_messages.content
        == "text post start<br/>***********<br/>text post end"
    )

    assert (
        post_with_image.content
        == '<img src="rss_path/images/channel/111.jpg" width="800"><br/>photo post start single'
    )

    assert (
        post_with_webpage.content
        == "webpage post single<br/>-------------------<br/>web title<br/>web descr<br/>"
        + '<img src="rss_path/images/channel/4.jpg" width="400"><br/>-------------------<br/>'
    )

    assert (
        post_with_document.content
        == "📦 MessageMediaDocument<br/>media document post single"
    )

    assert (
        post_with_ad.content == "text post with ad single #нативнаяинтеграция"
        and post_with_ad.title == "РЕКЛАМА text post with ad single #нативнаяинтеграция"
    )
