import json
import unittest
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse

from parameterized import parameterized

import direct_scraper

from direct_scraper import (
    get_hackathon,
    devpost,
    unternehmertum,
    huawei,
    n3xtcoder,
    taikai_network,
    Hackathon,
)


class TestScrapers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        direct_scraper.REQUESTS_DRY_RUN = True

    @parameterized.expand(
        [
            (get_hackathon, "https://hack.tum.de"),
            (get_hackathon, "https://hackfest.tech/"),
            (get_hackathon, "https://ethmunich.de/"),
            (get_hackathon, "https://hack.startmunich.de/events/rtsh"),
            (get_hackathon, "https://makeathon.tum-ai.com/"),
            (get_hackathon, "https://munihac.de"),
            (get_hackathon, "https://www.cassini.eu/hackathons/"),
            (get_hackathon, "https://imprs-astro-hackathon.de/"),
            (get_hackathon, "https://www.pushquantum.tech/pq-hackathon"),
            (get_hackathon, "https://hackathon.radiology.bayer.com/"),
            (get_hackathon, "https://www.hackbay.de/"),
            (unternehmertum, "https://www.unternehmertum.de"),
        ]
    )
    @patch("direct_scraper.requests.get")
    def test_get_html(self, scraper, url, mock_get):
        host = urlparse(url).netloc
        with open(f"data/{host}.html", encoding="utf-8") as file:
            mock_get.return_value = MagicMock(status_code=200, text=file.read())
        with open(f"expected/{host}.json", encoding="utf-8") as file:
            expected = json.load(file, object_hook=lambda x: Hackathon(**x))

        result = scraper(url)
        self.assertListEqual(expected, result)

    @parameterized.expand(
        [
            (devpost, "devpost.com"),
            (huawei, "huawei.agorize.com"),
            (n3xtcoder, "n3xtcoder.org"),
        ]
    )
    @patch("direct_scraper.requests.get")
    def test_get_json(self, scraper, host, mock_get):
        with open(f"data/{host}.json", encoding="utf-8") as file:
            load = json.load(file)
            mock_get.return_value = MagicMock(status_code=200, json=lambda: load)
        with open(f"expected/{host}.json", encoding="utf-8") as file:
            expected = json.load(file, object_hook=lambda x: Hackathon(**x))

        result = scraper(None)
        self.assertListEqual(expected, result)

    @parameterized.expand(
        [
            (taikai_network, "api.taikai.network"),
        ]
    )
    @patch("direct_scraper.requests.post")
    def test_post_json(self, scraper, host, mock_post):
        with open(f"data/{host}.json", encoding="utf-8") as file:
            load = json.load(file)
            mock_post.return_value = MagicMock(status_code=200, json=lambda: load)
        with open(f"expected/{host}.json", encoding="utf-8") as file:
            expected = json.load(file, object_hook=lambda x: Hackathon(**x))

        result = scraper(None)
        self.assertListEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
