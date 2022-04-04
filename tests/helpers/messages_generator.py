import datetime

from telethon.tl.patched import Message
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaWebPage,
    WebPage,
    Photo,
    MessageMediaDocument,
)


# "2021-12-07T00:05:23+00:00" -> datetime
def datetime_from_string(s):
    return datetime.datetime.fromisoformat(s)


# timestamp -> string
# 1649068165 -> "2021-12-07T00:05:23+00:00"
def timestamp_to_datetime_string(ts):
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.isoformat()


# date: "2021-12-07T00:05:23+00:00"
def gen_message(idx, text, date, media=None):
    m = Message(idx, media=media)
    m.text = text
    m.date = datetime_from_string(date)
    return m


def gen_message_media_photo(idx):
    return MessageMediaPhoto(
        photo=Photo(
            id=idx, access_hash=0, file_reference=b"ref", date=None, sizes=[], dc_id=0
        )
    )


def gen_message_media_web_page(idx, title, description):
    return MessageMediaWebPage(
        webpage=WebPage(
            id=idx,
            url="url",
            display_url="display_url",
            hash=0,
            title=title,
            description=description,
            photo=Photo(
                id=idx,
                access_hash=0,
                file_reference=b"ref",
                date=None,
                sizes=[],
                dc_id=0,
            ),
        )
    )


def gen_message_media_document():
    return MessageMediaDocument(document=None)
