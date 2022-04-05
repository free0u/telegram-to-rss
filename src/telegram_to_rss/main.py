import time
from pathlib import Path

from telegram_to_rss.heartbeat import send_heartbeat
from telegram_to_rss.posts.converter import (
    messages_to_posts,
    get_grouped_posts,
)
from telegram_to_rss.rss.rss_generator import make_rss, generate_channel_subscribe_list
from telegram_to_rss.telegram.channels import (
    load_channels_info,
    ChannelAccessInfo,
)
from telegram_to_rss.telegram.messages import load_channels_posts


def process_channel(channel_access_info: ChannelAccessInfo):
    # 0 create dirs
    Path("./rss/" + channel_access_info.name).mkdir(parents=True, exist_ok=True)
    Path("./images/" + channel_access_info.name).mkdir(parents=True, exist_ok=True)

    # 1 load messages from telegram
    telegram_messages = load_channels_posts(channel_access_info)

    # 2 convert messages to single posts
    single_posts = messages_to_posts(channel_access_info, telegram_messages)

    # 3 get grouped posts for rss
    grouped_posts = get_grouped_posts(single_posts)

    # 4 dump rss files
    make_rss(channel_access_info, grouped_posts)

    print("CHANNEL ", channel_access_info, "done")
    time.sleep(5)


def main():
    channels = load_channels_info("channels_test.txt")
    # channels = load_channels_info("channels.txt")

    for c in channels:
        process_channel(c)

    generate_channel_subscribe_list(channels)
    send_heartbeat()


if __name__ == "__main__":
    main()
