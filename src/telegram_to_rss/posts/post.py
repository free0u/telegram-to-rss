import datetime
from dataclasses import dataclass


@dataclass
class Post:
    title: str
    content: str
    url: str
    date: datetime
