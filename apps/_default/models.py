"""
This file defines the database models
"""

from datetime import datetime

from py4web import Field
from pydal.validators import IS_URL, IS_IN_SET

from aggregator import Aggregator
from direct_scraper import DirectScraper
from .common import db

db.define_table(
    "hackathon",
    Field("url", "string", unique=True, requires=IS_URL()),
    Field("image", "string"),
    Field("name", "string"),
    Field("description", "text"),
    Field("date", "string"),
    Field("location", "string"),
    format="%(url)s",
)

values = [e.value for e in DirectScraper] + [e.value for e in Aggregator]
names = ["Direct " + e.name for e in DirectScraper] + [
    "Aggregator " + e.name for e in Aggregator
]
db.define_table(
    "scraper",
    Field("url", "string", unique=True, requires=IS_URL()),
    Field("direct", "boolean", notnull=True),
    Field(
        "type",
        "integer",
        notnull=True,
        requires=[IS_IN_SET(values, names, zero=names[0])],
    ),
    Field("last_scraped", "datetime"),
    Field("next_run", "reference task_run"),
    Field("from_scraper", "reference scraper"),
    format="%(url)s",
)

db.define_table(
    "suggestion",
    Field("image", "string"),
    Field("name", "string"),
    Field("description", "text"),
    Field("date", "string"),
    Field("location", "string"),
    Field("created_at", "datetime", default=datetime.now),
    Field("hackathon_id", "reference hackathon", notnull=True),
    Field("from_scraper", "reference scraper", notnull=True),
)

db.commit()
