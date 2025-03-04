import re

import requests
from bs4 import BeautifulSoup

url = "https://hack.tum.de"

name = "What is the name of the hackathon?"
location = "Where is the hackathon?"
date = "When is the hackathon?"
topics = "What topics does the hackathon center around?"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    text = re.sub(r"\s+", " ", soup.text.strip())
    with open("hack.html", "w") as f:
        f.write(str(soup.html))
    with open("hack.txt", "w") as f:
        f.write(soup.text)
    with open("hack.clean.txt", "w") as f:
        f.write(text)

    description = soup.find("meta", attrs={"name": "description"})
    if description and description.get("content"):
        print(description["content"])

else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
