import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from llm_support import fill_in
from models import Hackathon


def html(url: str):
    response = requests.get(url)
    if response.ok:
        return BeautifulSoup(response.text, "html.parser")
    print(
        f"Failed to scrape {url}, status code: {response.status_code}, reason: {response.reason}"
    )


def json(url: str):
    response = requests.get(url)
    if response.ok:
        try:
            return response.json()
        except Exception as e:
            print(f"Failed to parse JSON from {url}: {e}")
    print(
        f"Failed to scrape {url}, status code: {response.status_code}, reason: {response.reason}"
    )


def get_hackathon(url: str) -> Hackathon:
    soup = html(url)
    hack = Hackathon(url, "", "", "", "", "")
    for meta in soup.find_all("meta"):
        match meta.get("property"):
            case "og:image":
                hack.image = meta["content"]
            case "og:title":
                hack.name = meta["content"]
            case "og:description":
                hack.description = meta["content"]
            case "og:url":
                hack.url = meta["content"]
            case "og:site_name":
                hack.location = meta["content"]

    print(hack)
    text = soup.find("body").get_text("\n", strip=True)
    return fill_in(hack, text)


def get_from_aggregator(url) -> set[str]:
    soup = html(url)
    return {
        urljoin(url, a["href"])
        for a in soup.find_all("a", href=True)
        if "hackathon" in a["href"].lower()
    }


def devpost():
    data = json(
        "https://devpost.com/api/hackathons?open_to[]=public&search=munich&status[]=upcoming&status[]=open"
    )
    for hack in data["hackathons"]:
        hackathons.append(
            Hackathon(
                url=hack["url"],
                image=hack["thumbnail_url"],
                name=hack["title"],
                description=f"Prize: {hack['prize_amount']}, Registrations: {hack['registrations_count']}",
                date=hack["submission_period_dates"],
                location=hack["displayed_location"]["location"],
            )
        )


def tumthinktank():
    soup = html(
        "https://tumthinktank.de/wp-admin/admin-ajax.php?action=wpcss_load_more_posts&type=cpt_event&offset=0&exclude=&more=1"
    )
    i = 8
    while re.search(r"Show \d+ more", soup.text):
        links = soup.find_all("a", href=True)
        sources.add(
            urljoin("https://tumthinktank.de/", a["href"])
            for a in links
            if "hackathon" in a["href"].lower()
        )
        soup = html(
            f"https://tumthinktank.de/wp-admin/admin-ajax.php?action=wpcss_load_more_posts&type=cpt_event&offset={i}&exclude=&more=1"
        )
        i += 8


def unternehmertum():
    soup = html("https://www.unternehmertum.de/events?filter%5B%5D=9511")
    table_list = soup.find(class_="table-list")
    for event in table_list.find_all("li"):
        url = event.find("a")["href"]
        date = event.find("div", class_="col-12 lg:col-2").get_text(strip=True)
        name = event.find("h3").get_text(strip=True)
        description = event.find("div", class_="mb-20 sm:mb-30").get_text(strip=True)

        hackathons.append(
            Hackathon(url=url, image="", name=name, description=description, date=date)
        )


def tum_venture_labs():
    soup = html(
        "https://www.tum-venture-labs.de/index.php?p=actions/sprig-core/components/render&eventFormats%5B%5D=66989&sprig%3AsiteId=9a1761719fed643d2a9161f9bfa109521c7487343e041b2d3541f6f497b907ed1&sprig%3Aid=18f5b0bbf1163c3ee576f32b2b84820f55e7f2099ee44df628295be00ca478d4s-events-list&sprig%3Acomponent=7b3a1f07361ad5a76557bad89bff243735691e7103956a9201f2c2959b531556&sprig%3Atemplate=49f84ea3b95926b92ef6f0545f1b9613962135886d4703c8e69d52dcaacc4088events%2F_event-list"
    )
    links = soup.find_all("a", href=True)
    sources.add(urljoin("https://www.tum-venture-labs.de/", a["href"]) for a in links)


def huawei():
    data = json("https://huawei.agorize.com/api/v2/challenges")
    for item in data['data']:
        attributes = item['attributes']
        hackathon = Hackathon(
            url=f"https://huawei.agorize.com/{attributes['slug']}",
            image=attributes['board_image_url'],
            name=attributes['name'],
            description=attributes['summary'],
            date=f"{attributes['start_at']} - {attributes['create_or_join_team_allowed_until']}",
            location="",
        )
        hackathons.append(hackathon)
    if not data['meta']['page']['last_page']:
        print("implement paging for Huawei")


def n3xtcoder():
    try:
        data = requests.get(
            "https://n3xtcoder.org/api/event-cards?offset=0&sort=desc&pageSize=6&lang=en"
        ).json()
    except Exception as e:
        print(f"Failed to get hackathons from n3xtcoder: {e}")
        return
    for card in data["data"]["cards"]:
        if card["typeOfEvent"] != "hackathon":
            continue
        time = card["timeFrame"]
        hackathon = Hackathon(
            url=urljoin("https://n3xtcoder.org/", card["slug"]),
            image="assets/n3xtcoder.png",
            name=card["title"],
            description="",
            date=f"{time[["starttime"]]} - {time["endtime"]}",
            location="",
        )
        hackathons.append(hackathon)


hackathons = []

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

for aggregator in aggregators:
    print(f"Getting hackathons from {aggregator}...")
    sources |= get_from_aggregator(aggregator)

devpost()
tum_venture_labs()

print(f"Found {len(sources)} hackathons: {sources}")

for source in sources:
    print(f"Scraping {source}...")
    hackathon = get_hackathon(source)
    print(hackathon)
