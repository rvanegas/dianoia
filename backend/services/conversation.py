# mypy: disable-error-code=call-overload
from dataclasses import dataclass
from typing import Optional
from config import OPENAI_API_KEY, OPENAI_MODEL
from core.utils import logger
from services.openaiclient import client

from .system_prompt import (
    theses_system_prompt,
    justify_system_prompt,
    evaluate_system_prompt)

@dataclass
class Gpt:
    instructions: str
    response_format_base: dict
    assistant_id: Optional[str] = None

    def __post_init__(self):
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": self.response_format_base
            }
        }
        response = client.beta.assistants.create(
            model=OPENAI_MODEL,
            tools=[{"type": "file_search"}],
            instructions=self.instructions,
            response_format=response_format)
        self.assistant_id = response.id

    # def call(self, prompt: str):
    #     messages = [{
    #         "role": "user",
    #         "content": "Help me with the argument."
    #     }]
    #     response_format = {
    #         "format": {
    #             "type": "json_schema",
    #             "name": "response",
    #             "strict": True,
    #             "schema": self.response_format_base
    #         }        
    #     }
    #     response = client.responses.create(
    #         model=OPENAI_MODEL,
    #         input=messages,
    #         text=response_format
    #     )
    #     return response.output_text

    def call(self, prompt: str, vector_store_id: str):
        # logger.debug(f"vs {vector_store_id}")
        thread={
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }
        if vector_store_id != None:
            thread["tool_resources"] = {
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            }
        run = client.beta.threads.create_and_run_poll(
            thread=thread,
            assistant_id=self.assistant_id,
        )
        messages = client.beta.threads.messages.list(
            thread_id=run.thread_id)
        # logger.debug(f"m {messages}")
        for message in reversed(messages.data):
            if message.role == "assistant":
                return message.content[0].text.value
        raise RuntimeError("no assistant value found")

gpt_theses = Gpt(
    instructions=theses_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "thesis": {"type": "string"},
            "counter_thesis": {"type": "string"},
            "presupposition": {"type": "string"}
        },
        "required": ["thesis", "counter_thesis", "presupposition"],
        "additionalProperties": False
    }
)

gpt_justify = Gpt(
    instructions=justify_system_prompt,
    response_format_base={
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
)

gpt_evaluate = Gpt(
    instructions=evaluate_system_prompt,
    response_format_base={
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
)
