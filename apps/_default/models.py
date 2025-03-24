"""
This file defines the database models
"""

from datetime import datetime

from py4web import Field
from pydal.validators import IS_URL

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

db.define_table(
    "scraper",
    Field("url", "string", unique=True, requires=IS_URL()),
    Field("direct", "boolean", notnull=True),
    Field("type", "integer", notnull=True),
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
