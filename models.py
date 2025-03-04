from dataclasses import dataclass


@dataclass
class Hackathon:
    url: str
    image: str
    name: str
    description: str
    date: str
    location: str = ""
