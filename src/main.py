import json
import pickle
import time
from pathlib import Path

import requests
import telethon.sync
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from telethon import TelegramClient
from telethon.errors import ChannelInvalidError
from telethon.tl.types import InputPeerChannel, MessageMediaPhoto, MessageMediaWebPage

from src.config import Config

OFFLINE = False
telegram_client = None

config = Config()


def getTelegramClient():
    s = telethon.sync.__all__
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


def extractTitle(text):
    soup = BeautifulSoup(text, features="lxml")
    all_text = "".join(soup.findAll(text=True))
    return all_text.split("\n")[0][:80]


def dumpMessagesToDisk(messages):
    cookie_path = "messages.pkl"
    with open(cookie_path, "wb") as f:
        pickle.dump(messages, f)


def getMessagesFromDisk():
    cookie_path = "messages.pkl"
    try:
        with open(cookie_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


def loadChannelsPosts(channel, entity):
    # if OFFLINE:
    #     loaded = getMessagesFromDisk()
    #     for m in loaded:
    #         print(m)
    #     return loaded

    print("loadChannelsPosts")
    print(str(channel) + " " + str(entity))
    client = getTelegramClient()
    t = client.get_messages(entity, limit=15)

    messages = list(t)

    messages_json = [m.to_json() for m in messages]

    message = messages[0]

    # print(messages_json)
    # dumpMessagesToDisk(messages_json)
    # exit(0)
    return messages


def isAd(post):
    if "#нативнаяинтеграция" in post["text"]:
        return True
    if "РЕКЛАМИЩЕ ВЕЛИКОЕ" in post["title"]:
        return True
    return False


## here parsing telegram post to inner object
def messageToPost(message, channel):
    text = ""
    if message.text is not None:
        text = message.text
    title = extractTitle(text)
    text = text.replace("\n", "<br/>")

    date = message.date
    mediaType = ""

    if len(title) == 0:
        title = str(message.id)
    print(date, title)
    # print(message.to_json())
    post = {}
    if message.media:
        needAddTag = True

        if isinstance(message.media, MessageMediaPhoto):
            needAddTag = False
            image = message.photo

            photoPath = "./images/" + channel + "/" + str(image.id) + ".jpg"
            my_file = Path(photoPath)
            if my_file.is_file():
                pass
            else:
                message.download_media(file=photoPath)
            imgTag = (
                '<img src="' + config.urls.rss_path + photoPath[2:] + '" width="800">'
            )
            text = imgTag + "<br/>" + text
        # print(text)
        if isinstance(message.media, MessageMediaWebPage):
            needAddTag = False

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
                    photoPath = "./images/" + channel + "/" + str(image.id) + ".jpg"
                    my_file = Path(photoPath)
                    if my_file.is_file():
                        pass
                    else:
                        message.download_media(file=photoPath)
                    imgTag = (
                        '<img src="'
                        + config.urls.rss_path
                        + photoPath[2:]
                        + '" width="400">'
                    )
                    text += imgTag

                text += "<br/>-------------------<br/>"
            pass
        # if isinstance(message.media, MessageMediaDocument):
        #     print(message.document.to_json())
        #     print(message.video)
        #     print(message.file)
        #     pass

        if needAddTag:
            mediaType = str(type(message.media).__name__)
            text = "📦 " + mediaType + "<br/>" + text

    post["text"] = text
    post["title"] = str(title)
    post["mediaType"] = mediaType
    post["date"] = date
    post["url"] = "https://t.me/" + channel + "/" + str(message.id)

    if isAd(post):
        post["title"] = "РЕКЛАМА {}".format(post["title"])

    return post


def getPosts(channel, entity):
    posts = []
    messages = loadChannelsPosts(channel, entity)
    for message in messages:
        post = messageToPost(message, channel)
        if post is not None:
            posts.append(post)

    return posts


def makeRss(channel, entity):
    posts = getPosts(channel, entity)
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
        if len(cur) > 1:
            last_post = cur[1]["date"]
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

    print("start generate rss file")
    fg = FeedGenerator()
    fg.title(channel)
    fg.description(channel)
    fg.link(href="https://t.me/s/" + channel, rel="alternate")
    fg.link(href=config.urls.rss_path + channel + "/rss.xml", rel="self")
    for p in posts:
        # print(p)

        fe = fg.add_entry()
        fe.title(p["title"])
        fe.pubDate(p["date"])
        fe.id(p["url"])
        fe.content(content=p["text"])
        fe.link(href=p["url"])

    fileName = "./rss/" + channel + "/rss.xml"
    fileNameDebug = "./rss/" + "debug" + "/rss.xml"
    # print(fileName)
    fg.rss_file(fileName, encoding="UTF-8")
    fg.rss_file(fileNameDebug, encoding="UTF-8")
    print("stop generate rss file")


def removeChannelFromCache(channel_name):
    channel_info = {}
    with open("channels_info.json", "r") as json_file:
        channel_info = json.load(json_file)

    if channel_info.pop(channel_name, None) is not None:
        with open("channels_info.json", "w") as outfile:
            json.dump(channel_info, outfile, sort_keys=True, indent=4)


def loadChannelsInfo(channel_list_file):
    channel_names = []
    with open(channel_list_file, "r") as f:
        channel_names = f.readlines()

    channel_names = list(map(lambda s: s.strip(), channel_names))

    channel_names = list(
        filter(lambda s: not s.startswith("#") and len(s) > 0, channel_names)
    )
    print(channel_names)

    channel_info = {}
    with open("channels_info.json", "r") as json_file:
        channel_info = json.load(json_file)

    changed = False
    for channel_name in channel_names:
        if not channel_name in channel_info:
            print("new channel_name: " + channel_name)
            user = getTelegramClient().get_input_entity(channel_name)
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


def sendHeartbeat():
    h = config.urls.heartbeat_auth.split(":")
    headers = {h[0]: h[1]}
    r = requests.get(config.urls.heartbeat_path, headers=headers, timeout=10)


def main():
    # channels = loadChannelsInfo("channels_test.txt")
    channels = loadChannelsInfo("channels.txt")

    for c in channels:
        try:
            Path("./rss/" + c[0]).mkdir(parents=True, exist_ok=True)
            Path("./images/" + c[0]).mkdir(parents=True, exist_ok=True)
            makeRss(c[0], c[1])
            print("CHANNEL ", c, "done")
            time.sleep(5)
        except ChannelInvalidError as e:
            with open("error.log.txt", "a") as f:
                f.write("ChannelInvalidError " + str(c) + "\n")
            print("CHANNEL " + str(c) + " fail" + str(e))
            removeChannelFromCache(c[0])
            print("removed channel {} from cache.info".format(c[0]))
            exit(1)

    with open("./rss/all/index.html", "w") as f:
        for c in channels:
            url = config.urls.rss_path + "rss/" + c[0] + "/rss.xml"
            print(url)
            f.write('<a href="{}">{}</a></br>\n'.format(url, url))

    sendHeartbeat()


main()
