from dataclasses import dataclass

@dataclass
class Note():
    nid: int
    title: str
    note: str
    author_name: str
    author_profile: str