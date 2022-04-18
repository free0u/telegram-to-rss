from telethon.errors import ChannelInvalidError

from telegram_to_rss.telegram.channels import remove_channel_from_cache
from telegram_to_rss.telegram.client import get_telegram_client


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


def load_channels_posts(channel_access_info):
    try:
        channel, entity = channel_access_info.name, channel_access_info.access_info
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
        # exit(1)

        print("loadChannelsPosts")
        print(str(channel) + " " + str(entity))
        client = get_telegram_client()
        t = client.get_messages(entity, limit=30)

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

    except ChannelInvalidError as e:
        with open("error.log.txt", "a") as f:
            f.write("ChannelInvalidError " + str(channel_access_info) + "\n")
        print("CHANNEL " + str(channel_access_info) + " fail" + str(e))
        remove_channel_from_cache(channel_access_info.name)
        print("removed channel {} from cache.info".format(channel_access_info.name))
        exit(1)
