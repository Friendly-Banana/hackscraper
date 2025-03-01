import requests
from bs4 import BeautifulSoup
import re

#from general import ask_llm

url = 'https://hack.tum.de'

#from transformers import pipeline

#qa_model = pipeline("question-answering", "timpal0l/mdeberta-v3-base-squad2")
name = "What is the name of the hackathon?"
location = "Where is the hackathon?"
date = "On which date does the hackathon take place?"
topics = "What topics does the hackathon center around?"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    text = re.sub(r"\n{2,}", "\n", soup.text.strip())
    with open("hack.html", "w") as f:
        f.write(str(soup.html))
    with open("hack.txt", "w") as f:
        f.write(soup.text)
    #qa_model(question = location, context = text)
    #print(ask_llm(url, text))
else:
    print(f'Failed to retrieve the webpage. Status code: {response.status_code}')