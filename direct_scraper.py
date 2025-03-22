import logging
from enum import Enum
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from llm_support import fill_in
from models import Hackathon


def html(url: str):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def json(url: str):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def split_title(hack: Hackathon, title: str):
    parts = title.replace("–", "-").split(" - ")
    hack.name = parts[0].strip()
    if len(parts) > 1 and not hack.description:
        hack.description = " - ".join(parts[1:])


def get_hackathon(url: str) -> list[Hackathon]:
    soup = html(url)
    hack = Hackathon(url, "", "", "", "", "")
    for meta in soup.find_all("meta"):
        match meta.get("property"):
            case "og:image":
                hack.image = meta["content"]
            case "og:title":
                split_title(hack, meta["content"])
            case "og:description":
                hack.description = meta["content"]
            case "og:url":
                hack.url = meta["content"]
            case "og:site_name":
                hack.location = meta["content"]

    text = soup.find("body").get_text("\n", strip=True)
    llm_hack = Hackathon(url, "", "", "", "", "")
    llm_suggestion = fill_in(llm_hack, text)
    logging.info(hack, llm_suggestion)
    return [hack, llm_suggestion]


def devpost(_url: str) -> list[Hackathon]:
    data = json(
        "https://devpost.com/api/hackathons?open_to[]=public&search=munich&status[]=upcoming&status[]=open"
    )
    hacks = []
    for hack in data["hackathons"]:
        hacks.append(
            Hackathon(
                url=hack["url"],
                image="https:" + hack["thumbnail_url"],
                name=hack["title"],
                description=", ".join(theme["name"] for theme in hack["themes"]),
                date=hack["submission_period_dates"],
                location=hack["displayed_location"]["location"],
            )
        )
    return hacks


def unternehmertum(_url: str) -> list[Hackathon]:
    hacks = []
    soup = html("https://www.unternehmertum.de/events?filter%5B%5D=9511")
    table_list = soup.find(class_="table-list")
    for event in table_list.find_all("li"):
        url = event.find("a")["href"]
        date = event.find("div", class_="col-12 lg:col-2").get_text(strip=True)
        name = event.find("h3").get_text(strip=True)
        description = event.find("div", class_="mb-20 sm:mb-30").get_text(strip=True)
        hacks.append(
            Hackathon(url=url, image="", name=name, description=description, date=date)
        )
    return hacks


def huawei(_url: str) -> list[Hackathon]:
    hacks = []
    data = json("https://huawei.agorize.com/api/v2/challenges")
    for item in data["data"]:
        attributes = item["attributes"]
        hacks.append(
            Hackathon(
                url=f"https://huawei.agorize.com/{attributes['slug']}",
                image=attributes["board_image_url"],
                name=attributes["name"],
                description=attributes["summary"],
                date=f"{attributes['start_at']} - {attributes['create_or_join_team_allowed_until']}",
                location="",
            )
        )
    if not data["meta"]["page"]["last_page"]:
        logging.warning("should implement paging for Huawei")
    return hacks


def n3xtcoder(_url: str) -> list[Hackathon]:
    hacks = []
    data = json(
        "https://n3xtcoder.org/api/event-cards?offset=0&sort=desc&pageSize=6&lang=en"
    )
    for card in data["data"]["cards"]:
        if card["typeOfEvent"] != "hackathon":
            continue
        time = card["timeFrame"]
        hack = Hackathon(
            url=urljoin("https://n3xtcoder.org/", card["slug"]),
            image="assets/n3xtcoder.png",
            name="",
            description="",
            date=f"{time['starttime']} - {time['endtime']}",
            location="",
        )
        split_title(hack, card["title"])
        hacks.append(hack)
    return hacks


def taikai_network(_url):
    url = "https://api.taikai.network/api/graphql"
    headers = {"Referer": "https://taikai.network/", "Origin": "https://taikai.network"}
    payload = {
        "operationName": "ALL_CHALLENGES_QUERY",
        "variables": {
            "sortBy": {
                "order": "desc",
            },
            "page": 1,
        },
        "query": "query ALL_CHALLENGES_QUERY($sortBy: ChallengeOrderByWithRelationInput, $page: Int) {  challenges(where: {publishInfo: {state: {equals: ACTIVE}}, isClosed: {equals: false}}, page: $page, orderBy: $sortBy) {\n    id\n    name\n    isClosed\n    shortDescription\n    cardImageFile {\n      id\n      url\n      __typename\n    }\n    organization {\n      id\n      name\n      slug\n      __typename\n    }\n    steps {\n      id\n      startDate\n      __typename\n    }\n    currentStep {\n      id\n      name\n      startDate\n      __typename\n    }\n    slug\n    order\n    __typename\n  }\n}",
    }
    response = requests.post(url, headers=headers, payload=payload)
    response.raise_for_status()
    data = response.json()
    hacks = []
    for challenge in data["data"]["challenges"]:
        hacks.append(
            Hackathon(
                url=f"https://taikai.network/{challenge['organization']['slug']}/hackathons/{challenge['slug']}",
                image=challenge["cardImageFile"]["url"],
                name=challenge["name"],
                description=challenge["shortDescription"],
                date=challenge["steps"][-1]["startDate"],
                location="",
            )
        )

    return hacks


class DirectScraper(Enum):
    LLM = -1
    GENERIC = 0
    DEVPOST = 1
    UNTERNEHMER_TUM = 2
    HUAWEI = 3
    N3XTCODER = 4
    TAIKAI_NETWORK = 5


direct_scrapers = {
    DirectScraper.GENERIC: get_hackathon,
    DirectScraper.DEVPOST: devpost,
    DirectScraper.UNTERNEHMER_TUM: unternehmertum,
    DirectScraper.HUAWEI: huawei,
    DirectScraper.N3XTCODER: n3xtcoder,
    DirectScraper.TAIKAI_NETWORK: taikai_network,
}
