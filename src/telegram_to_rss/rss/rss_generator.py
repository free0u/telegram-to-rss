from feedgen.feed import FeedGenerator

from telegram_to_rss.config import config
from telegram_to_rss.posts.post import Post
from telegram_to_rss.telegram.channels import ChannelAccessInfo


def make_rss(channel_access_info: ChannelAccessInfo, posts: [Post]):
    channel = (
        channel_access_info.name
    )  # posts = get_grouped_posts_from_channel(channel, entity)

    print("start generate rss file")
    fg = FeedGenerator()
    fg.title(channel)
    fg.description(channel)
    fg.link(href="https://t.me/s/" + channel, rel="alternate")
    fg.link(href=config().urls.rss_path + channel + "/rss.xml", rel="self")
    for p in posts:
        fe = fg.add_entry()
        fe.title(p.title)
        fe.pubDate(p.date)
        fe.id(p.url)
        fe.content(content=p.content)
        fe.link(href=p.url)

    # file_name = "./rss/" + channel + "/rss.xml"
    file_name = "./rss/{}/rss.xml".format(channel)
    file_name_debug = "./rss/" + "debug" + "/rss.xml"
    # print(file_name)
    fg.rss_file(file_name, encoding="UTF-8")
    fg.rss_file(file_name_debug, encoding="UTF-8")
    print("stop generate rss file")


def generate_channel_subscribe_list(channels):
    with open("./rss/all/index.html", "w") as f:
        for c in channels:
            url = config().urls.rss_path + "rss/" + c.name + "/rss.xml"
            print(url)
            f.write('<a href="{}">{}</a></br>\n'.format(url, url))
