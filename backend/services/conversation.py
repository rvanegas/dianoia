# mypy: disable-error-code=call-overload
from dataclasses import dataclass

from config import OPENAI_API_KEY
from core.utils import logger
from services.openaiclient import client

from .system_prompt import (
    theses_system_prompt,
    justify_system_prompt,
    evaluate_system_prompt)

@dataclass
class Gpt:
    system_prompt: str
    response_format: dict

    def call(self, prompt: str):
        messages = [{
            "role": "developer",
            "content": self.system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }]
        response = client.responses.create(
            model="gpt-4o",
            input=messages,
            text=self.response_format
            # tools=[]
        )
        return response.output_text

gpt_theses = Gpt(
    system_prompt=theses_system_prompt,
    response_format={
        "format": {
            "type": "json_schema",
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

gpt_justify = Gpt(
    system_prompt=justify_system_prompt,
    response_format={
        "format": {
            "type": "json_schema",
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
        "format": {
            "type": "json_schema",
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
