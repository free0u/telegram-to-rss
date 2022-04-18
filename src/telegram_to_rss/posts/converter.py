import time
from pathlib import Path

from bs4 import BeautifulSoup
from telethon.tl.types import MessageMediaPhoto, MessageMediaWebPage

from telegram_to_rss.config import config
from telegram_to_rss.posts.post import Post
from telegram_to_rss.posts.template import env


def extract_title(text):
    soup = BeautifulSoup(text, features="lxml")
    all_text = "".join(soup.findAll(text=True))
    return all_text.split("\n")[0][:80]


def is_ad(title, content):
    if "#нативнаяинтеграция" in content:
        return True
    if "РЕКЛАМИЩЕ ВЕЛИКОЕ" in title:
        return True
    return False


def download_photo_if_not_exists(message, path):
    my_file = Path(path)
    if not my_file.is_file():
        message.download_media(file=path)


def get_post_image(message, channel):
    if message.media:
        if isinstance(message.media, MessageMediaPhoto):
            image = message.photo

            photo_path = "./images/{}/{}.jpg".format(channel, str(image.id))
            download_photo_if_not_exists(message, photo_path)
            img_tag = '<img src="{}{}" width="800">'.format(
                config().urls.rss_path, photo_path[2:]
            )
            return {"tag": img_tag}
    return None


# TODO
# no image|title|descr case
def get_post_webpage(message, channel):
    if message.media:
        if isinstance(message.media, MessageMediaWebPage):
            if message.web_preview:
                # preview info
                webpage = {}
                if message.web_preview.title:
                    webpage["title"] = message.web_preview.title
                if message.web_preview.description:
                    webpage["description"] = message.web_preview.description

                image = message.photo
                if image:
                    photo_path = "./images/{}/{}.jpg".format(channel, str(image.id))
                    download_photo_if_not_exists(message, photo_path)
                    img_tag = '<img src="{}{}" width="400">'.format(
                        config().urls.rss_path, photo_path[2:]
                    )
                    webpage["image"] = img_tag
                return webpage
    return None


def get_post_media_type(message):
    if message.media:
        media_type = str(type(message.media).__name__)
        return {"media_type": media_type}
    return None


# here parsing telegram post to inner object
def message_to_post(message, channel):
    # text
    text = ""
    if message.text is not None:
        text = message.text
    text = text.replace("\n", "<br/>")

    # title
    title = extract_title(text)
    if len(title) == 0:
        title = str(message.id)
    if is_ad(title, text):
        title = "РЕКЛАМА {}".format(title)

    # date
    date = message.date

    # url
    url = "https://t.me/{}/{}".format(channel, str(message.id))

    print(date, title)

    # insert media in text
    image = get_post_image(message, channel)
    webpage = get_post_webpage(message, channel)
    if image is None and webpage is None:
        general_media = get_post_media_type(message)
    else:
        general_media = None

    one_post_template = env.get_template("one_post.txt")
    text = one_post_template.render(
        content=text,
        image=image,
        webpage=webpage,
        general_media=general_media,
    )
    text = text.replace("\n", "")

    return Post(title, text, url, date)


def messages_to_posts(channel_access_info, messages):
    channel = channel_access_info.name
    posts = []
    # messages = load_channels_posts(channel, entity)
    for message in messages:
        post = message_to_post(message, channel)
        if post is not None:
            posts.append(post)

    return posts


def get_grouped_posts(posts: [Post]):
    # posts = get_posts(channel, entity)
    n = len(posts)

    print("\n\nGroup processing")
    groups = [[]]
    # TODO iterate from old to last and break group each 7 (for example) posts
    # to break long chains. or NOT?
    if n != 0:
        groups = []
        cur = [posts[0]]
        for i in range(1, n):
            # reverse order
            prev_date = posts[i].date
            cur_date = posts[i - 1].date
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

    # remove oldest group
    if len(groups) > 0:
        groups = groups[:-1]
        pass

    # remove newest group if too new
    if len(groups) > 0:
        cur = groups[0]
        if len(cur) > 0:  # > 1
            last_post = cur[0].date  # 1
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
            print(j.date, j.title)

    posts = []
    for group in groups:
        if len(group) == 0:
            continue

        cur_group = list(reversed(group))
        first_post = cur_group[0]

        common_text = "<br/>***********<br/>".join(map(lambda x: x.content, cur_group))

        first_post.content = common_text
        print(first_post)

        posts.append(first_post)

    return posts
