import re
from enum import Enum
from urllib.parse import urljoin

from direct_scraper import html


def get_links(url: str) -> set[str]:
    soup = html(url)
    return {
        urljoin(url, a["href"])
        for a in soup.find_all("a", href=True)
        if "hackathon" in a["href"].lower()
    }


def tum_think_tank(_url: str) -> set[str]:
    soup = html(
        "https://tumthinktank.de/wp-admin/admin-ajax.php?action=wpcss_load_more_posts&type=cpt_event&offset=0&exclude=&more=1"
    )
    urls = set()
    i = 8
    while re.search(r"Show \d+ more", soup.text):
        for a in soup.find_all("a", href=True):
            if "hackathon" in a["href"].lower():
                urls.add(urljoin("https://tumthinktank.de/", a["href"]))
        soup = html(
            f"https://tumthinktank.de/wp-admin/admin-ajax.php?action=wpcss_load_more_posts&type=cpt_event&offset={i}&exclude=&more=1"
        )
        i += 8
    return urls


def tum_venture_labs(_url: str) -> set[str]:
    soup = html(
        "https://www.tum-venture-labs.de/index.php?p=actions/sprig-core/components/render&eventFormats%5B%5D=66989&sprig%3AsiteId=9a1761719fed643d2a9161f9bfa109521c7487343e041b2d3541f6f497b907ed1&sprig%3Aid=18f5b0bbf1163c3ee576f32b2b84820f55e7f2099ee44df628295be00ca478d4s-events-list&sprig%3Acomponent=7b3a1f07361ad5a76557bad89bff243735691e7103956a9201f2c2959b531556&sprig%3Atemplate=49f84ea3b95926b92ef6f0545f1b9613962135886d4703c8e69d52dcaacc4088events%2F_event-list"
    )
    links = soup.find_all("a", href=True)
    return {urljoin("https://www.tum-venture-labs.de/", a["href"]) for a in links}


class AggregatorType(Enum):
    GENERIC = 0
    TUM_THINK_TANK = 1
    TUM_VENTURE_LABS = 2


aggregator_scrapers = {
    AggregatorType.GENERIC: get_links,
    AggregatorType.TUM_THINK_TANK: tum_think_tank,
    AggregatorType.TUM_VENTURE_LABS: tum_venture_labs,
}
