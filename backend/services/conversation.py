from enum import Enum
from dataclasses import dataclass
from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger

from .system_prompt import (
    theses_system_prompt,
    develop_system_prompt,
    justify_system_prompt,
    evaluate_system_prompt)

client = OpenAI(api_key=OPENAI_API_KEY)

@dataclass
class Gpt:
    system_prompt: dict
    response_format: str

    def call(self, prompt: str):
        messages = [{
            "role": "system",
            "content": self.system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format=self.response_format,
        )
        return response.choices[0].message.content

gpt_theses = Gpt(
    system_prompt=theses_system_prompt,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "thesis": {"type": "string"},
                    "counter_thesis": {"type": "string"},
                    "presupposition": {"type": "string"}
                },
                "required": ["thesis", "counter_thesis", "presupposition"],
                "additionalProperties": False
            }
        }
    }
)

argument_format = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "index": {"type": "string"},
            "proposition": {"type": "string"},
            "justifiers": {
                "type": "array",
                "items": {"type": "string"}
            },
            "truth": {"type": "number"},
            "valid": {"type": "number"}
        },
        "required": ["index", "proposition", "justifiers", "truth", "valid"],
        "additionalProperties": False
    }
}

gpt_develop = Gpt(
    system_prompt=develop_system_prompt,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "assumptions": argument_format,
                    "argument": argument_format,
                    "counter_argument": argument_format
                },
                "required": ["argument", "counter_argument", "assumptions"],
                "additionalProperties": False
            }
        }
    }
)

gpt_justify = Gpt(
    system_prompt=justify_system_prompt,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "propositions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["propositions"],
                "additionalProperties": False
            }
        }
    }
)

gpt_evaluate = Gpt(
    system_prompt=evaluate_system_prompt,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "truth": {
                        "type": "array",
                        "items": {"type": "number"}
                    },
                    "valid": {"type": "number"}
                },
                "required": ["truth", "valid"],
                "additionalProperties": False
            }
        }
    }
)
