import requests

from telegram_to_rss.config import config


def send_heartbeat():
    h = config().urls.heartbeat_auth.split(":")
    headers = {h[0]: h[1]}
    requests.get(config().urls.heartbeat_path, headers=headers, timeout=10)
