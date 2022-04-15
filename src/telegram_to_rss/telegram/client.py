from telethon.sync import TelegramClient

from telegram_to_rss.config import config

OFFLINE = False
telegram_client = None


def get_telegram_client():
    global telegram_client
    if telegram_client:
        return telegram_client
    if not OFFLINE:
        api_id = config().telegram_creds.api_id
        api_hash = config().telegram_creds.api_hash

        client = TelegramClient("session_name", api_id, api_hash)
        client.parse_mode = "html"
        client.start()
        telegram_client = client

    return telegram_client
