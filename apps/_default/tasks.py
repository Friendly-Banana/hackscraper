import dataclasses

from aggregator import aggregator_scrapers, Aggregator
from direct_scraper import direct_scrapers, DirectScraper
from .common import scheduler, settings, logger
from .models import db


def run_scraper(**inputs):
    scraper = db.scraper[inputs["scraper"]]
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
                        without_url = dataclasses.asdict(hack)
                        without_url.pop("url")
                        db.suggestion.update_or_insert(
                            **without_url,
                            hackathon_id=existing.id,
                            from_scraper=scraper.id,
                        )
                        suggestions += 1
                else:
                    db.hackathon.update_or_insert(**dataclasses.asdict(hack))
                    new += 1
            result = f"{new} hackathons, {suggestions} suggestions"
        else:
            aggregator = Aggregator(scraper.type)
            logger.info("Scraping aggregator %s with %s", scraper.url, aggregator)
            scrape = aggregator_scrapers[aggregator]
            links = scrape(scraper.url)
            result = str(links)

            for link in links:
                db.scraper.update_or_insert(
                    url=link,
                    direct=True,
                    type=0,
                    from_scraper=scraper.id,
                )
        db.commit()
    except BaseException as e:
        logger.error("Failed to scrape %s", scraper.url, exc_info=e)
        # rollback on failure
        db.rollback()
        raise
    return result


# Use the built-in scheduler (nothing to install)
if settings.USE_SCHEDULER:
    scheduler.register_task("run_scraper", run_scraper)

# Optionally configure Celery
elif settings.USE_CELERY:
    # To use celery tasks:
    # 1) pip install -U "celery[redis]"
    # 2) In settings.py:
    # USE_CELERY = True
    # CELERY_BROKER = "redis://localhost:6379/0"
    # 3) Start "redis-server"
    # 4) Start "celery -A apps.{appname}.tasks beat"
    # 5) Start "celery -A apps.{appname}.tasks worker --loglevel=info" for each worker

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
