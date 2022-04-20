import datetime
import time
from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path

from telegram_to_rss.config import init_config
from telegram_to_rss.heartbeat import send_heartbeat
from telegram_to_rss.posts.converter import (
    messages_to_posts,
    get_grouped_posts,
)
from telegram_to_rss.posts.template import env
from telegram_to_rss.rss.rss_generator import make_rss, generate_channel_subscribe_list
from telegram_to_rss.telegram.channels import (
    load_channels_info,
    ChannelAccessInfo,
)
from telegram_to_rss.telegram.messages import load_channels_posts


@dataclass
class Stat:
    channel_name: str
    first_date: datetime
    last_date: datetime
    posts_by_day: float
    posts_num: int
    telegram_url: str
    rss_url: str


stats = []


def process_channel(channel_access_info: ChannelAccessInfo):
    # 0 create dirs
    Path("./rss/" + channel_access_info.name).mkdir(parents=True, exist_ok=True)
    Path("./images/" + channel_access_info.name).mkdir(parents=True, exist_ok=True)

    # 1 load messages from telegram
    telegram_messages = load_channels_posts(channel_access_info)
    # telegram_messages = []

    # 2 convert messages to single posts
    single_posts = messages_to_posts(channel_access_info, telegram_messages)

    # 3 get grouped posts for rss
    grouped_posts = get_grouped_posts(single_posts)

    # 4 dump rss files
    make_rss(channel_access_info, grouped_posts)

    # 5 get stats
    day_diff = single_posts[0].date - single_posts[-1].date
    print("day diff: {} {}", day_diff, day_diff.days)
    print("len(posts): {}", len(single_posts))
    stat = Stat(
        channel_name=channel_access_info.name,
        first_date=single_posts[-1].date.astimezone(
            datetime.timezone(datetime.timedelta(hours=3))
        ),
        last_date=single_posts[0].date.astimezone(
            datetime.timezone(datetime.timedelta(hours=3))
        ),
        posts_by_day=len(single_posts) * 1.0 / day_diff.days,
        posts_num=len(single_posts),
        telegram_url="https://t.me/s/{}".format(channel_access_info.name),
        rss_url="https://anton-evdokimov.ru/trss/rss/{}/rss.xml".format(
            channel_access_info.name
        ),
    )
    stats.append(stat)

    print("CHANNEL ", channel_access_info, "done")
    time.sleep(5)


def dump_stats():
    template = env.get_template("channels_stat.html")
    # print(template.render(the="variables", go="here"))

    global stats
    stats = list(sorted(stats, key=attrgetter("last_date"), reverse=True))
    template.stream(stats=stats).dump("./rss/all/stats.html")


def main():
    init_config()
    channels = load_channels_info("channels_test.txt")
    # channels = load_channels_info("channels.txt")

    for c in channels:
        process_channel(c)

    dump_stats()

    template = env.get_template("all_rss.html")
    print(template)
    print(template.render(the="variables", go="here"))
    template.stream(links=["link1", "link2"]).dump("./rss/all/index2.html")

    generate_channel_subscribe_list(channels)
    send_heartbeat()


if __name__ == "__main__":
    main()
