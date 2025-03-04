from transformers import pipeline

from models import Hackathon

name = "What is the name of the hackathon?"
description = "What is the hackathon about?"
date = "When is the hackathon?"
location = "Where is the hackathon?"

qa_model = pipeline("question-answering", "timpal0l/mdeberta-v3-base-squad2")


def ask(question: str, context: str):
    return qa_model(question=question, context=context)["answer"].strip()


def fill_in(hack: Hackathon, context: str):
    hack.name = ask(name, context)
    if not hack.description:
        hack.description = ask(description, context)

    hack.date = ask(date, context)
    hack.location = ask(location, context)
    return hack
