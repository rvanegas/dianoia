# mypy: disable-error-code=call-overload
from dataclasses import dataclass
from typing import Optional
import threading
import time

from config import OPENAI_MODEL
# from core.utils import logger
from services.openaiclient import client
from services.system_prompt import (
    theses_system_prompt,
    justify_system_prompt,
    evaluate_system_prompt,
    explain_system_prompt)

ASSISTANT_TTL = 24 * 60 * 60  # 24 hours

class Gpt:
    def __init__(self, instructions: str, response_format_base: str):
        self.instructions = instructions
        self.response_format_base = response_format_base
        self.assistant_id = None
        self.created_at = time.time()
        self.lock = threading.Lock()

    def get_assistant(self):
        with self.lock:
            if (self.assistant_id is None or
                (time.time() - self.created_at) > ASSISTANT_TTL):
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
                self.created_at = time.time()
            return self.assistant_id

    def call(self, prompt: str, vector_store_id: str):
        assistant_id = self.get_assistant()
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
            assistant_id=assistant_id,
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
            "presupposition": {"type": "string"},
            "name": {"type": "string"}
        },
        "required": ["thesis", "counter_thesis", "presupposition", "name"],
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
                "items": {"type": "string"}
            },
            "valid": {"type": "string"}
        },
        "required": ["truth", "valid"],
        "additionalProperties": False
    }
)

gpt_explain = Gpt(
    instructions=explain_system_prompt,
    response_format_base={
        "type": "object",
        "properties": {
            "formalization": {
                "type": "array",
                "items": {"type": "string"}
            },
            "explanation": {"type": "string"}
        },
        "required": ["formalization", "explanation"],
        "additionalProperties": False
    }
)
