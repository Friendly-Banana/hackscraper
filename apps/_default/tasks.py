import dataclasses
from datetime import datetime, timedelta

from aggregator import aggregator_scrapers, Aggregator
from direct_scraper import direct_scrapers, DirectScraper
from .common import scheduler, settings, logger
from .models import db


# #######################################################
# Use the built-in scheduler (nothing to install)
# #######################################################


def schedule_scraper():
    due = (
        db.scraper(db.scraper.last_scraped < datetime.now() - timedelta(days=30))(
            db.scraper.next_run is None
        )
        .select()
        .for_update()
    )
    for scraper in due:
        scheduler.queue_task("run_scraper", pvars={"scraper": scraper.id})
        scraper.update_record(next_run=datetime.now() + timedelta(days=30))


def run_scraper(**inputs):
    scraper = db.scraper[inputs["scraper"]]
    if not scraper:
        raise ValueError("Scraper not found")

    scraper.update_record(last_scraped=datetime.now())
    db.commit()
    try:
        if scraper.direct:
            direct_scraper = DirectScraper(scraper.type)
            logger.info("Directly scraping %s with %s", scraper.url, direct_scraper)
            scrape = direct_scrapers[direct_scraper]
            hackathons = scrape(scraper.url)
            suggestions, new = 0, 0

            # Upsert hackathons
            for hack in hackathons:
                existing = db(db.hackathon.url == hack.url).select().first()
                if existing:
                    if (
                        existing.image != hack.image
                        or existing.name != hack.name
                        or existing.description != hack.description
                        or existing.date != hack.date
                        or existing.location != hack.location
                    ):
                        db.suggestion.insert(
                            **dataclasses.asdict(hack),
                            hackathon_id=existing.id,
                            scraper_id=scraper.id,
                        )
                        suggestions += 1
                else:
                    db.hackathon.insert(
                        **dataclasses.asdict(hack), scraper_id=scraper.id
                    )
                    new += 1
            result = f"{new} new hackathons, {suggestions} suggestions"
        else:
            aggregator = Aggregator(scraper.type)
            logger.info("Scraping aggregator %s with %s", scraper.url, aggregator)
            scrape = aggregator_scrapers[aggregator]
            links = result = scrape(scraper.url)

            for link in links:
                db.scraper.update_or_insert(
                    (db.scraper.url == link),
                    direct=True,
                    type=0,
                    url=link,
                    from_scraper=scraper.id,
                )
        db.commit()
    except BaseException as e:
        logger.error("Failed to scrape %s", scraper.url, exc_info=e)
        # rollback on failure
        db.rollback()
        raise
    return result


if settings.USE_SCHEDULER:
    scheduler.register_task("schedule_scraper", schedule_scraper)
    scheduler.register_task("run_scraper", run_scraper)

# #######################################################
# Optionally configure Celery
# #######################################################
elif settings.USE_CELERY:
    # #######################################################
    # To use celery tasks:
    # 1) pip install -U "celery[redis]"
    # 2) In settings.py:
    # USE_CELERY = True
    # CELERY_BROKER = "redis://localhost:6379/0"
    # 3) Start "redis-server"
    # 4) Start "celery -A apps.{appname}.tasks beat"
    # 5) Start "celery -A apps.{appname}.tasks worker --loglevel=info" for each worker
    # #######################################################

    from celery import Celery

    # to use "from .common import scheduler" and then use it according
    # to celery docs, examples in tasks.py
    celery_scheduler = Celery(
        "apps.%s.tasks" % settings.APP_NAME, broker=settings.CELERY_BROKER
    )

    # register your tasks
    @scheduler.task
    def my_task():
        # reconnect to database
        db._adapter.reconnect()
        try:
            # do something here
            db.commit()
        except:
            # rollback on failure
            db.rollback()

    # run my_task every 10 seconds
    celery_scheduler.conf.beat_schedule = {
        "my_first_task": {
            "task": f"apps.{settings.APP_NAME}.tasks.my_task",
            "schedule": 10.0,
            "args": (),
        },
    }
