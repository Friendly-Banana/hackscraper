from dataclasses import dataclass
from typing import List
from json import loads

@dataclass
class Hackathon:
    url: str
    name: str
    start: str
    end: str
    location: str
    topics: List[str]

from llama_cpp import Llama

llm = Llama.from_pretrained(
    repo_id="Qwen/Qwen2-0.5B-Instruct-GGUF",
    filename="*q8_0.gguf",
    verbose=False
)

def ask_llm(url: str, text: str):
    answer = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": "Output all relevant data about the hackathon as JSON. Use ISO dates.",
            },
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_object",
            "schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "start": {"type": "string"}, "end": {"type": "string"}, "location": {"type": "string"}, "topics": {"type": "array", "items": {"type": "string"}}},
                "required": ["name", "start", "end", "location", "topics"],
            },
        },
        temperature=0.7,
    )
    response = answer["choices"][0]["message"]["content"]
    data = loads(response)
    return Hackathon(url, data["name"], data["start"], data["end"], data["location"], data["topics"])
