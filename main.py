import logging
import sqlite3

from aggregator import AggregatorType, aggregator_scrapers
from config import DEFAULT_SCRAPE_FREQUENCY
from direct_scraper import DirectScraperType, direct_scrapers
from models import ScraperModel, Hackathon, HackathonModel

logging.basicConfig(level=logging.INFO)

con = sqlite3.connect("hackathon.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys = ON")
cur.execute("""
CREATE TABLE IF NOT EXISTS scraper(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direct BOOLEAN NOT NULL,
    type INTEGER NOT NULL,
    url TEXT UNIQUE,
    last_scraped DATETIME,
    next_scrape DATE,
    from_scraper INTEGER,
    FOREIGN KEY (from_scraper) REFERENCES scraper(id)
)
""")
# LLM suggestions
cur.execute(
    """INSERT INTO scraper (id, direct, type, url, next_scrape) VALUES (0, true, ?, 'LLM', NULL) ON CONFLICT DO NOTHING""",
    (DirectScraperType.LLM,),
)
cur.execute("""
CREATE TABLE IF NOT EXISTS hackathon(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    image TEXT,
    name TEXT,
    description TEXT,
    date TEXT,
    location TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS suggestion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image TEXT,
    name TEXT,
    description TEXT,
    date TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hackathon_id INTEGER,
    scraper_id INTEGER,
    FOREIGN KEY (scraper_id) REFERENCES scraper(id),
    FOREIGN KEY (hackathon_id) REFERENCES hackathon(id)
)
""")
con.commit()


def upsert_hackathons(hackathons: list[Hackathon], scraper: ScraperModel):
    for hack in hackathons:
        existing = cur.execute(
            "SELECT * FROM hackathon WHERE url = ?", (hack.url,)
        ).fetchone()
        if existing:
            ex = HackathonModel(*existing)
            if (
                ex.image != hack.image
                or ex.name != hack.name
                or ex.description != hack.description
                or ex.date != hack.date
                or ex.location != hack.location
            ):
                cur.execute(
                    """INSERT INTO suggestion (image, name, description, date, location, hackathon_id, scraper_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        hack.image,
                        hack.name,
                        hack.description,
                        hack.date,
                        hack.location,
                        ex.id,
                        scraper.id,
                    ),
                )
        else:
            cur.execute(
                """INSERT INTO hackathon (url, image, name, description, date, location, scraper_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    hack.url,
                    hack.image,
                    hack.name,
                    hack.description,
                    hack.date,
                    hack.location,
                    scraper.id,
                ),
            )


def insert_scraper(links: set[str]):
    for link in links:
        cur.execute(
            "INSERT INTO scraper (direct, type, url, next_scrape, from_scraper) VALUES (true, 0, ?, current_timestamp, ?) ON CONFLICT DO NOTHING",
            (link, scraper.id),
        )


cur.execute("""
        SELECT * FROM scraper
        WHERE next_scrape < current_timestamp
    """)
all_scraper: list[ScraperModel] = list(map(lambda s: ScraperModel(*s), cur.fetchall()))
logging.info("Fetching %d pages...", len(all_scraper))

for scraper in all_scraper:
    try:
        if scraper.direct:
            scrape = direct_scrapers[DirectScraperType(scraper.type)]
        else:
            scrape = aggregator_scrapers[AggregatorType(scraper.type)]
        links_or_hackathons = scrape(scraper.url)
    except Exception as e:
        logging.exception("Page %s failed:", scraper.url, exc_info=e)
    else:
        if scraper.direct:
            upsert_hackathons(links_or_hackathons, scraper)
        else:
            insert_scraper(links_or_hackathons)
    finally:
        cur.execute(
            "UPDATE scraper SET last_scraped=current_timestamp, next_scrape=datetime(current_timestamp, ?) WHERE id=?",
            (DEFAULT_SCRAPE_FREQUENCY, scraper.id,),
        )
        con.commit()

logging.info("Fetching pages done")
