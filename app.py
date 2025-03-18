import sqlite3

from flask import Flask, render_template, request, redirect

from aggregator import AggregatorType
from config import DEFAULT_SCRAPE_FREQUENCY
from direct_scraper import DirectScraperType

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("hackathon.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    conn = get_db_connection()
    hackathons = conn.execute("SELECT * FROM hackathon").fetchall()
    conn.close()
    return render_template("index.html", hackathons=hackathons)


@app.route("/admin")
def admin():
    conn = get_db_connection()
    hackathons = conn.execute("SELECT * FROM hackathon").fetchall()
    conn.close()
    return render_template("admin.html", hackathons=hackathons)


@app.route("/scrapers")
def scrapers():
    conn = get_db_connection()
    scrapers = conn.execute("SELECT * FROM scraper").fetchall()
    conn.close()

    direct_types = {t.value: t.name for t in DirectScraperType}
    aggregator_types = {t.value: t.name for t in AggregatorType}

    return render_template(
        "scrapers.html",
        scrapers=scrapers,
        direct_types=direct_types,
        aggregator_types=aggregator_types
    )


@app.route("/scraper/<int:scraper_id>", methods=["GET", "POST"])
def edit_scraper(scraper_id):
    conn = sqlite3.connect("hackathon.db")
    conn.row_factory = sqlite3.Row

    if request.method == "POST":
        direct = "direct" in request.form
        scraper_type = int(request.form["type"])
        url = request.form["url"]

        conn.execute(
            "UPDATE scraper SET direct = ?, type = ?, url = ? WHERE id = ?",
            (direct, scraper_type, url, scraper_id)
        )
        conn.commit()
        conn.close()
        return redirect("/scrapers")

    # GET request - show edit form
    scraper = conn.execute(
        "SELECT * FROM scraper WHERE id = ?", (scraper_id,)
    ).fetchone()

    if scraper is None:
        conn.close()
        return "Scraper not found", 404

    from direct_scraper import DirectScraperType
    from aggregator import AggregatorType

    direct_scraper_types = list(DirectScraperType)
    aggregator_scraper_types = list(AggregatorType)

    conn.close()
    return render_template(
        "edit_scraper.html",
        scraper=scraper,
        direct_scraper_types=direct_scraper_types,
        aggregator_scraper_types=aggregator_scraper_types
    )


@app.route("/scraper/<int:scraper_id>/delete", methods=["POST"])
def delete_scraper(scraper_id):
    conn = sqlite3.connect("hackathon.db")
    conn.execute("DELETE FROM scraper WHERE id = ?", (scraper_id,))
    conn.commit()
    conn.close()
    return redirect("/scrapers")


@app.route("/scraper/<int:id>/run", methods=["POST"])
def run_scraper(id):
    from direct_scraper import direct_scrapers, DirectScraperType
    from aggregator import aggregator_scrapers, AggregatorType
    from models import ScraperModel
    import logging

    conn = get_db_connection()
    scraper_data = conn.execute("SELECT * FROM scraper WHERE id = ?", (id,)).fetchone()

    if not scraper_data:
        logging.debug("Scraper not found")
        conn.close()
        return redirect("/scrapers")

    scraper = ScraperModel(*scraper_data)
    logging.debug("Scraping %s", scraper.url)
    try:
        if scraper.direct:
            scrape = direct_scrapers[DirectScraperType(scraper.type)]
            links_or_hackathons = scrape(scraper.url)

            # Upsert hackathons
            for hack in links_or_hackathons:
                existing = conn.execute(
                    "SELECT * FROM hackathon WHERE url = ?", (hack.url,)
                ).fetchone()
                if existing:
                    if (
                            existing["image"] != hack.image
                            or existing["name"] != hack.name
                            or existing["description"] != hack.description
                            or existing["date"] != hack.date
                            or existing["location"] != hack.location
                    ):
                        conn.execute(
                            """INSERT INTO suggestion (image, name, description, date, location, hackathon_id, scraper_id) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                hack.image,
                                hack.name,
                                hack.description,
                                hack.date,
                                hack.location,
                                existing["id"],
                                scraper.id,
                            ),
                        )
                else:
                    conn.execute(
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
        else:
            scrape = aggregator_scrapers[AggregatorType(scraper.type)]
            links = scrape(scraper.url)

            for link in links:
                conn.execute(
                    "INSERT INTO scraper (direct, type, url, next_scrape, from_scraper) VALUES (true, 0, ?, current_timestamp, ?) ON CONFLICT DO NOTHING",
                    (link, scraper.id),
                )
    except Exception as e:
        logging.exception(f"Page {scraper.url} failed:", exc_info=e)
    finally:
        conn.execute(
            "UPDATE scraper SET last_scraped=current_timestamp, next_scrape=datetime(current_timestamp, ?) WHERE id=?",
            (DEFAULT_SCRAPE_FREQUENCY, scraper.id,),
        )
        conn.commit()
        conn.close()

    return redirect("/scrapers")


@app.route("/add_hackathon", methods=["GET", "POST"])
def add_hackathon():
    if request.method == "POST":
        url = request.form["url"]
        image = request.form["image"]
        name = request.form["name"]
        description = request.form["description"]
        date = request.form["date"]
        location = request.form["location"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO hackathon (url, image, name, description, date, location) VALUES (?, ?, ?, ?, ?, ?)",
            (url, image, name, description, date, location),
        )
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_hackathon.html")


@app.route("/hackathon/<int:hackathon_id>/delete", methods=["POST"])
def delete_hackathon(hackathon_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM hackathon WHERE id = ?", (hackathon_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/suggestions")
def suggestions():
    conn = get_db_connection()
    suggestions = conn.execute("SELECT * FROM suggestion").fetchall()
    conn.close()
    return render_template("suggestions.html", suggestions=suggestions)


@app.route("/suggestion/<int:id>", methods=["GET", "POST"])
def suggestion_detail(id):
    conn = get_db_connection()
    suggestion = conn.execute("SELECT * FROM suggestion WHERE id = ?", (id,)).fetchone()
    hackathon = conn.execute(
        "SELECT * FROM hackathon WHERE id = ?", (suggestion["hackathon_id"],)
    ).fetchone()

    if request.method == "POST":
        fields_to_update = {}
        for field in ["image", "name", "description", "date", "location"]:
            if request.form.get(f"accept_{field}"):
                fields_to_update[field] = suggestion[field]

        if fields_to_update:
            set_clause = ", ".join(
                [f"{field} = ?" for field in fields_to_update.keys()]
            )
            values = list(fields_to_update.values()) + [hackathon["id"]]
            conn.execute(f"UPDATE hackathon SET {set_clause} WHERE id = ?", values)
            conn.commit()

        conn.execute("DELETE FROM suggestion WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return redirect("/suggestions")

    conn.close()
    return render_template(
        "suggestion_detail.html", suggestion=suggestion, hackathon=hackathon
    )


@app.route("/add_scraper", methods=["GET", "POST"])
def add_scraper():
    if request.method == "POST":
        direct = request.form.get("direct") == "true"
        scraper_type = int(request.form["type"])
        url = request.form["url"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO scraper (direct, type, url, next_scrape, from_scraper) VALUES (?, ?, ?, current_timestamp, NULL)",
            (direct, scraper_type, url),
        )
        conn.commit()
        conn.close()
        return redirect("/scrapers")

    direct_scraper_types = list(DirectScraperType)
    aggregator_scraper_types = list(AggregatorType)
    return render_template(
        "add_scraper.html",
        direct_scraper_types=direct_scraper_types,
        aggregator_scraper_types=aggregator_scraper_types,
        default_scrape_frequency=DEFAULT_SCRAPE_FREQUENCY,
    )


if __name__ == "__main__":
    app.run(debug=True)
