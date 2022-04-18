import json
from dataclasses import dataclass

from telethon.tl.types import InputPeerChannel

from telegram_to_rss.telegram.client import get_telegram_client

CHANNELS_INFO_JSON = "channels_info.json"


@dataclass
class ChannelAccessInfo:
    name: str
    access_info: InputPeerChannel


def _remove_channel_from_cache_impl(file_name, channel_name):
    # channel_info = {}
    with open(file_name, "r") as json_file:
        channel_info = json.load(json_file)

    if channel_info.pop(channel_name, None) is not None:
        with open(file_name, "w") as outfile:
            json.dump(channel_info, outfile, sort_keys=True, indent=4)
            return True

    return False


def remove_channel_from_cache(channel_name):
    _remove_channel_from_cache_impl(CHANNELS_INFO_JSON, channel_name)


def _load_channels_info_impl(file_name, channel_list_file):
    # channel_names = []
    with open(channel_list_file, "r") as f:
        channel_names = f.readlines()

    channel_names = list(map(lambda s: s.strip(), channel_names))

    channel_names = list(
        filter(lambda s: not s.startswith("#") and len(s) > 0, channel_names)
    )
    print(channel_names)

    # channel_info = {}
    with open(file_name, "r") as json_file:
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
        with open(file_name, "w") as outfile:
            json.dump(channel_info, outfile, sort_keys=True, indent=4)

    channels = []
    for channel_name in channel_names:
        info = channel_info[channel_name]
        user = InputPeerChannel(info["channel_id"], info["access_hash"])
        # channels.append([channel_name, user])
        channels.append(ChannelAccessInfo(channel_name, user))
        print(channel_name + ": " + str(user))

    return channels


def load_channels_info(channel_list_file):
    return _load_channels_info_impl(CHANNELS_INFO_JSON, channel_list_file)
