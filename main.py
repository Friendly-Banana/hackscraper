import logging
import sqlite3

from aggregator import AggregatorType, aggregator_scrapers
from direct_scraper import DirectScraperType, direct_scrapers
from models import ScraperModel

sources = {
    "https://hack.tum.de",
    "https://hackfest.tech/",
    "https://ethmunich.de/",
    "https://hack.startmunich.de/events/rtsh",
    "https://makeathon.tum-ai.com/",
    "https://munihac.de",
    "https://www.cassini.eu/hackathons/",
    # 403 "https://eudis-hackathon.eu/",
    "https://imprs-astro-hackathon.de/",
    "https://www.pushquantum.tech/pq-hackathon",
    "https://hackathon.radiology.bayer.com/",
    "https://www.hackbay.de/",
}

aggregators = {
    "https://roboinnovate.mirmi.tum.de/",
    "https://opensource.construction/#events",
    "https://germantechjobs.de/events",
    "https://www.bayern-innovativ.de/events-termine/",
    "https://www.munich-urban-colab.de/events",
    "https://www.mdsi.tum.de/mdsi/aktuelles/veranstaltungen/",
    "https://veranstaltungen.muenchen.de/rit/",
    "https://www.tum-blockchain.com/events-category/hackathon",
}

DEFAULT_SCRAPE_FREQUENCY = "30 days"
LLM_SUGGESTION = -1

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
    frequency INTERVAL,
    from_scraper INTEGER,
    FOREIGN KEY (from_scraper) REFERENCES scraper(id)
)
""")
# LLM suggestions
cur.execute(
    """INSERT INTO scraper (id, direct, type, next_scrape) VALUES (?, true, -1, NULL) ON CONFLICT DO NOTHING""", (LLM_SUGGESTION,)
)
cur.execute("""
CREATE TABLE IF NOT EXISTS hackathon(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    image TEXT,
    name TEXT,
    description TEXT,
    date DATE,
    location TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS suggestion(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image TEXT,
    name TEXT,
    description TEXT,
    date DATE,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hackathon_id INTEGER,
    scraper_id INTEGER,
    FOREIGN KEY (scraper_id) REFERENCES scraper(id),
    FOREIGN KEY (hackathon_id) REFERENCES hackathon(id)
)
""")
con.commit()

cur.execute("""
        SELECT * FROM scraper
        WHERE NOT direct AND next_scrape < current_timestamp
    """)
aggregators: list[ScraperModel] = list(map(lambda a: ScraperModel(*a), cur.fetchall()))
logging.info("Fetching %d aggregators...", len(aggregators))

for agg in aggregators:
    scraper = aggregator_scrapers[AggregatorType(agg.type)]
    try:
        links = scraper(agg.url)
    except Exception as e:
        logging.exception("Aggregator %s failed:", agg.url, exc_info=e)
        continue
    cur.executemany(
        f"""INSERT INTO scraper (direct, type, url, next_scrape, frequency, from_scraper) VALUES (true, 0, ?, current_timestamp, {DEFAULT_SCRAPE_FREQUENCY}, {agg.id}) ON CONFLICT DO NOTHING""",
        links,
    )
    cur.execute(
        "UPDATE scraper SET last_scraped=current_timestamp, next_scrape=datetime(current_timestamp, frequency || ' days') WHERE id=?",
        (agg.id,),
    )
    con.commit()

logging.info("Fetching aggregators done")

cur.execute("""
        SELECT * FROM scraper
        WHERE direct AND next_scrape < current_timestamp
    """)
pages: list[ScraperModel] = list(map(lambda a: ScraperModel(*a), cur.fetchall()))
logging.info("Fetching %d pages...", len(pages))

for page in pages:
    scraper = direct_scrapers[DirectScraperType(page.type)]
    try:
        hackathons = scraper(page.url)
    except Exception as e:
        logging.exception("Page %s failed:", page.url, exc_info=e)
    else:
        for hack in hackathons:
            existing = cur.execute("SELECT * FROM hackathon WHERE url = ?", (hack.url,)).fetchone()
            if existing:
                cur.execute(
                    """INSERT INTO suggestion (image, name, description, date, location, hackathon_id, scraper_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (hack.image, hack.name, hack.description, hack.date, hack.location, existing[0], scraper.id))
            else:
                cur.execute(
                    """INSERT INTO hackathon (url, image, name, description, date, location, scraper_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (hack.url, hack.image, hack.name, hack.description, hack.date, hack.location, scraper.id))
    finally:
        cur.execute(
            "UPDATE scraper SET last_scraped=current_timestamp, next_scrape=datetime(current_timestamp, frequency || ' days') WHERE id=?",
            (page.id,),
        )
        con.commit()

logging.info("Fetching pages done")
