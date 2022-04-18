import time
from pathlib import Path

from bs4 import BeautifulSoup
from telethon.tl.types import MessageMediaPhoto, MessageMediaWebPage

from telegram_to_rss.config import config
from telegram_to_rss.posts.post import Post


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


def process_media_and_modify_content(message, channel, content):
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
                '<img src="'
                + config().urls.rss_path
                + photo_path[2:]
                + '" width="800">'
            )
            content = img_tag + "<br/>" + content
        # print(text)
        if isinstance(message.media, MessageMediaWebPage):
            need_add_tag = False

            if message.web_preview:
                # preview info
                content += "<br/>-------------------<br/>"
                if message.web_preview.title:
                    content += message.web_preview.title
                    content += "<br/>"
                if message.web_preview.description:
                    content += message.web_preview.description
                    content += "<br/>"

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
                        + config().urls.rss_path
                        + photo_path[2:]
                        + '" width="400">'
                    )
                    content += img_tag

                content += "<br/>-------------------<br/>"
            pass
        # if isinstance(message.media, MessageMediaDocument):
        #     print(message.document.to_json())
        #     print(message.video)
        #     print(message.file)
        #     pass

        if need_add_tag:
            media_type = str(type(message.media).__name__)
            content = "📦 " + media_type + "<br/>" + content

    return content


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

    text = process_media_and_modify_content(message, channel, text)

    title = str(title)
    url = "https://t.me/" + channel + "/" + str(message.id)

    if is_ad(title, text):
        title = "РЕКЛАМА {}".format(title)

    return Post(
        title=title,
        content=text,
        url=url,
        date=date,
        media_type_str=media_type,
    )


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
    for i in range(len(groups)):
        cur = groups[i]
        cur = list(reversed(cur))
        if len(cur) == 0:
            continue

        p = cur[0]

        common_text = "<br/>***********<br/>".join(map(lambda x: x.content, cur))

        p.content = common_text
        print(p)

        posts.append(p)

    return posts
