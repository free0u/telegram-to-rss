import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from telethon.errors import ChannelInvalidError
from telethon.sync import TelegramClient
from telethon.tl.types import (
    InputPeerChannel,
    MessageMediaPhoto,
    MessageMediaWebPage,
)

from telegram_to_rss.config import Config

OFFLINE = False
telegram_client = None

config = None


def get_hello():
    return "hello"


def bye():
    return "Not " + get_hello()


def get_telegram_client():
    global telegram_client
    if telegram_client:
        return telegram_client
    if not OFFLINE:
        api_id = config.telegram_creds.api_id
        api_hash = config.telegram_creds.api_hash

        client = TelegramClient("session_name", api_id, api_hash)
        client.parse_mode = "html"
        client.start()
        telegram_client = client
    return telegram_client


def extract_title(text):
    soup = BeautifulSoup(text, features="lxml")
    all_text = "".join(soup.findAll(text=True))
    return all_text.split("\n")[0][:80]


# def dumpMessagesToDisk(messages):
#     cookie_path = "messages.pkl"
#     with open(cookie_path, "wb") as f:
#         pickle.dump(messages, f)
#
#
# def getMessagesFromDisk():
#     cookie_path = "messages.pkl"
#     try:
#         with open(cookie_path, "rb") as f:
#             return pickle.load(f)
#     except FileNotFoundError:
#         return None


def load_channels_posts(channel, entity):
    # if OFFLINE:
    #     loaded = getMessagesFromDisk()
    #     for m in loaded:
    #         print(m)
    #     return loaded
    # import telethon
    # msg = telethon.tl.custom.Message(id=1)
    # msg.text = "text"
    # return [msg]
    # return [1]

    print("loadChannelsPosts")
    print(str(channel) + " " + str(entity))
    client = get_telegram_client()
    t = client.get_messages(entity, limit=15)

    messages = list(t)

    # messages_json = [m.to_json() for m in messages]
    print(type(messages[0]))
    print(messages[0].to_dict())
    # exit(1)

    # messages_json = [m.to_json() for m in messages]
    #
    # message = messages[0]

    # print(messages_json)
    # dumpMessagesToDisk(messages_json)
    # exit(0)
    return messages


def is_ad(post):
    if "#нативнаяинтеграция" in post["text"]:
        return True
    if "РЕКЛАМИЩЕ ВЕЛИКОЕ" in post["title"]:
        return True
    return False


# here parsing telegram post to inner object
def message_to_post(message, channel):
    text = ""
    if message.text is not None:
        text = message.text
    title = extract_title(text)
    text = text.replace("\n", "<br/>")

    date = message.date
    media_type = ""

    if len(title) == 0:
        title = str(message.id)
    print(date, title)
    # print(message.to_json())
    post = {}
    if message.media:
        need_add_tag = True

        if isinstance(message.media, MessageMediaPhoto):
            need_add_tag = False
            image = message.photo

            photo_path = "./images/" + channel + "/" + str(image.id) + ".jpg"
            my_file = Path(photo_path)
            if my_file.is_file():
                pass
            else:
                message.download_media(file=photo_path)
            img_tag = (
                '<img src="' + config.urls.rss_path + photo_path[2:] + '" width="800">'
            )
            text = img_tag + "<br/>" + text
        # print(text)
        if isinstance(message.media, MessageMediaWebPage):
            need_add_tag = False

            if message.web_preview:
                # preview info
                text += "<br/>-------------------<br/>"
                if message.web_preview.title:
                    text += message.web_preview.title
                    text += "<br/>"
                if message.web_preview.description:
                    text += message.web_preview.description
                    text += "<br/>"

                image = message.photo
                if image:
                    # print(message.to_json())
                    photo_path = "./images/" + channel + "/" + str(image.id) + ".jpg"
                    my_file = Path(photo_path)
                    if my_file.is_file():
                        pass
                    else:
                        message.download_media(file=photo_path)
                    img_tag = (
                        '<img src="'
                        + config.urls.rss_path
                        + photo_path[2:]
                        + '" width="400">'
                    )
                    text += img_tag

                text += "<br/>-------------------<br/>"
            pass
        # if isinstance(message.media, MessageMediaDocument):
        #     print(message.document.to_json())
        #     print(message.video)
        #     print(message.file)
        #     pass

        if need_add_tag:
            media_type = str(type(message.media).__name__)
            text = "📦 " + media_type + "<br/>" + text

    post["text"] = text
    post["title"] = str(title)
    post["media_type"] = media_type
    post["date"] = date
    post["url"] = "https://t.me/" + channel + "/" + str(message.id)

    if is_ad(post):
        post["title"] = "РЕКЛАМА {}".format(post["title"])

    return post


def get_posts(channel, entity):
    posts = []
    messages = load_channels_posts(channel, entity)
    # print(messages[0].text)
    # print(messages[0].text111)
    # exit(0)
    for message in messages:
        post = message_to_post(message, channel)
        if post is not None:
            posts.append(post)

    return posts


def get_grouped_posts_from_channel(channel, entity):
    # return []
    posts = get_posts(channel, entity)
    n = len(posts)

    print("\n\nGroup processing")
    groups = [[]]
    if n != 0:
        groups = []
        cur = [posts[0]]
        for i in range(1, n):
            # reverse order
            prev_date = posts[i]["date"]
            cur_date = posts[i - 1]["date"]
            delta = cur_date.timestamp() - prev_date.timestamp()
            # print(delta)
            # print(type(cur_date))
            if delta > 60 * 10:  # new group
                groups.append(cur)
                cur = [posts[i]]
            else:  # cur group
                cur.append(posts[i])
        if len(cur) > 0:
            groups.append(cur)

    if len(groups) > 0:
        groups = groups[:-1]
        pass

    if len(groups) > 0:
        cur = groups[0]
        if len(cur) > 0:  # > 1
            last_post = cur[0]["date"]  # 1
            now = time.time()
            print("now", now)
            since_last_post = now - last_post.timestamp()
            print("since_last_post", since_last_post)
            if since_last_post < 60 * 11:
                groups = groups[1:]
                print("drop newest group")
                pass

    for i in range(len(groups)):
        print("Group: " + str(i))
        for j in groups[i]:
            print(j["date"], j["title"])

    posts = []
    for i in range(len(groups)):
        cur = groups[i]
        cur = list(reversed(cur))
        if len(cur) == 0:
            continue

        p = cur[0]

        common_text = "<br/>***********<br/>".join(map(lambda x: x["text"], cur))

        p["text"] = common_text
        print(p)

        posts.append(p)

    return posts


def make_rss(channel, entity):
    posts = get_grouped_posts_from_channel(channel, entity)

    print("start generate rss file")
    fg = FeedGenerator()
    fg.title(channel)
    fg.description(channel)
    fg.link(href="https://t.me/s/" + channel, rel="alternate")
    fg.link(href=config.urls.rss_path + channel + "/rss.xml", rel="self")
    for p in posts:
        fe = fg.add_entry()
        fe.title(p["title"])
        fe.pubDate(p["date"])
        fe.id(p["url"])
        fe.content(content=p["text"])
        fe.link(href=p["url"])

    file_name = "./rss/" + channel + "/rss.xml"
    file_name_debug = "./rss/" + "debug" + "/rss.xml"
    # print(file_name)
    fg.rss_file(file_name, encoding="UTF-8")
    fg.rss_file(file_name_debug, encoding="UTF-8")
    print("stop generate rss file")


def remove_channel_from_cache(channel_name):
    # channel_info = {}
    with open("channels_info.json", "r") as json_file:
        channel_info = json.load(json_file)

    if channel_info.pop(channel_name, None) is not None:
        with open("channels_info.json", "w") as outfile:
            json.dump(channel_info, outfile, sort_keys=True, indent=4)


def load_channels_info(channel_list_file):
    # channel_names = []
    with open(channel_list_file, "r") as f:
        channel_names = f.readlines()

    channel_names = list(map(lambda s: s.strip(), channel_names))

    channel_names = list(
        filter(lambda s: not s.startswith("#") and len(s) > 0, channel_names)
    )
    print(channel_names)

    # channel_info = {}
    with open("channels_info.json", "r") as json_file:
        channel_info = json.load(json_file)

    changed = False
    for channel_name in channel_names:
        if channel_name not in channel_info:
            print("new channel_name: " + channel_name)
            user = get_telegram_client().get_input_entity(channel_name)
            info = {"channel_id": user.channel_id, "access_hash": user.access_hash}
            channel_info[channel_name] = info
            changed = True

    if changed:
        with open("channels_info.json", "w") as outfile:
            json.dump(channel_info, outfile, sort_keys=True, indent=4)

    channels = []
    for channel_name in channel_names:
        info = channel_info[channel_name]
        user = InputPeerChannel(info["channel_id"], info["access_hash"])
        channels.append([channel_name, user])
        print(channel_name + ": " + str(user))

    return channels


def send_heartbeat():
    h = config.urls.heartbeat_auth.split(":")
    headers = {h[0]: h[1]}
    requests.get(config.urls.heartbeat_path, headers=headers, timeout=10)


def main():
    global config
    config = Config()
    channels = load_channels_info("channels_test.txt")
    # channels = load_channels_info("channels.txt")

    for c in channels:
        try:
            Path("./rss/" + c[0]).mkdir(parents=True, exist_ok=True)
            Path("./images/" + c[0]).mkdir(parents=True, exist_ok=True)
            make_rss(c[0], c[1])
            print("CHANNEL ", c, "done")
            time.sleep(5)
        except ChannelInvalidError as e:
            with open("error.log.txt", "a") as f:
                f.write("ChannelInvalidError " + str(c) + "\n")
            print("CHANNEL " + str(c) + " fail" + str(e))
            remove_channel_from_cache(c[0])
            print("removed channel {} from cache.info".format(c[0]))
            exit(1)

    with open("./rss/all/index.html", "w") as f:
        for c in channels:
            url = config.urls.rss_path + "rss/" + c[0] + "/rss.xml"
            print(url)
            f.write('<a href="{}">{}</a></br>\n'.format(url, url))

    send_heartbeat()


if __name__ == "__main__":
    main()
