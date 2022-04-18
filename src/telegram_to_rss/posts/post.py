import datetime
from dataclasses import dataclass


@dataclass
class Post:
    title: str
    content: str
    url: str
    date: datetime
    media_type_str: str
