import json
import logging
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from transformers import pipeline


@dataclass
class Hackathon:
    url: str
    image: str
    name: str
    description: str
    date: str
    location: str = ""


REQUESTS_DRY_RUN = False
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko; Hackscraper/0.1; hack.gabriels.cloud) Chrome/134.0.0.0 Safari/537.3"


def get_html(url: str):
    headers = {"User-Agent": USER_AGENT}
    if REQUESTS_DRY_RUN:
        host = urlparse(url).netloc
        with open(f"tests/data/{host}.html", encoding="utf-8") as file:
            return BeautifulSoup(file.read(), "html.parser")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_json(url: str):
    headers = {"User-Agent": USER_AGENT}
    if REQUESTS_DRY_RUN:
        host = urlparse(url).netloc
        with open(f"tests/data/{host}.json", encoding="utf-8") as file:
            return json.load(file)

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def post_json(url: str, body):
    headers = {"User-Agent": USER_AGENT}
    if REQUESTS_DRY_RUN:
        host = urlparse(url).netloc
        with open(f"tests/data/{host}.json", encoding="utf-8") as file:
            return json.load(file)

    response = requests.post(url, json=body, headers=headers)
    response.raise_for_status()
    return response.json()


def split_title(hack: Hackathon, title: str):
    parts = title.replace("–", "-").split(" - ")
    hack.name = parts[0].strip()
    if len(parts) > 1 and not hack.description:
        hack.description = " - ".join(parts[1:])


name = "What is the name of the hackathon?"
description = "What is the hackathon about?"
date = "When is the hackathon?"
location = "Where is the hackathon?"

qa_model = None


def ask(question: str, context: str) -> str:
    global qa_model
    if qa_model is None:
        qa_model = pipeline("question-answering", "timpal0l/mdeberta-v3-base-squad2")
    return qa_model(question=question, context=context)["answer"].strip()


def get_hackathon(url: str) -> list[Hackathon]:
    soup = get_html(url)
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
    # URL may have been set from meta tag
    llm_hack = Hackathon(
        hack.url,
        "",
        ask(name, text),
        ask(description, text),
        ask(date, text),
        ask(location, text),
    )
    llm_suggestion = llm_hack
    return [hack, llm_suggestion]


def devpost(_url: str) -> list[Hackathon]:
    data = get_json(
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
    soup = get_html("https://www.unternehmertum.de/events?filter%5B%5D=9511")
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
    data = get_json("https://huawei.agorize.com/api/v2/challenges")
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
    data = get_json(
        "https://n3xtcoder.org/api/event-cards?offset=0&sort=desc&pageSize=6&lang=en"
    )
    for card in data["data"]["cards"]:
        if card["typeOfEvent"] != "hackathon":
            continue
        time = card["timeFrame"]
        hack = Hackathon(
            url=urljoin("https://n3xtcoder.org/", card["slug"]),
            image="/static/n3xtcoder.png",
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
    body = {
        "operationName": "ALL_CHALLENGES_QUERY",
        "variables": {
            "sortBy": {
                "order": "desc",
            },
            "page": 1,
        },
        "query": "query ALL_CHALLENGES_QUERY($sortBy: ChallengeOrderByWithRelationInput, $page: Int) {  challenges(where: {publishInfo: {state: {equals: ACTIVE}}}, page: $page, orderBy: $sortBy) {\n    id\n    name\n    isClosed\n    shortDescription\n    cardImageFile {\n      id\n      url\n      __typename\n    }\n    organization {\n      id\n      name\n      slug\n      __typename\n    }\n    steps {\n      id\n      startDate\n      __typename\n    }\n    currentStep {\n      id\n      name\n      startDate\n      __typename\n    }\n    slug\n    order\n    __typename\n  }\n}",
    }
    data = post_json(url, body)
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
