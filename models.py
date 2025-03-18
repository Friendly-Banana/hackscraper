import datetime
from dataclasses import dataclass


@dataclass
class Hackathon:
    url: str
    image: str
    name: str
    description: str
    date: str
    location: str = ""


@dataclass
class HackathonModel:
    id: int
    url: str
    image: str
    name: str
    description: str
    date: str
    location: str
    scraper_id: int


@dataclass
class ScraperModel:
    id: int
    direct: bool
    type: int
    url: str
    last_scraped: datetime.datetime
    next_scrape: datetime.date
    from_scraper: int
