# Builtins
from dataclasses import dataclass
from datetime import datetime

# Internal
from models.user import User

@dataclass
class Backup():
    id: int
    date: datetime
    article_count: int
    author: User
    sha1: bytes
    fingerprint: bytes