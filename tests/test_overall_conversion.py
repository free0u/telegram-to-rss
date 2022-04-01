import pytest

from telegram_to_rss.main import get_posts


@pytest.fixture
def mock_load_channels_posts(mocker):
    mock = mocker.patch("telegram_to_rss.main.load_channels_posts")
    mock.return_value = []
    return mock


def test_conversion(mock_load_channels_posts):
    posts = get_posts(None, None)
    assert posts == []
