"""
This file defines the database models
"""
from datetime import datetime

from .common import Field, db
from pydal.validators import IS_URL

db.define_table(
    'scraper',
    Field('direct', 'boolean', notnull=True),
    Field('type', 'integer', notnull=True),
    Field('url', 'string', unique=True, requires=IS_URL()),
    Field('last_scraped', 'datetime'),
    Field('next_scrape', 'date'),
    Field('from_scraper', 'reference scraper'),
)

db.define_table(
    'hackathon',
    Field('url', 'string', notnull=True, unique=True),
    Field('image', 'string'),
    Field('name', 'string'),
    Field('description', 'text'),
    Field('date', 'string'),
    Field('location', 'string'),
)

db.define_table(
    'suggestion',
    Field('image', 'string'),
    Field('name', 'string'),
    Field('description', 'text'),
    Field('date', 'string'),
    Field('location', 'string'),
    Field('created_at', 'datetime', default=datetime.now),
    Field('hackathon_id', 'reference hackathon'),
    Field('from_scraper', 'reference scraper'),
)

db.commit()
