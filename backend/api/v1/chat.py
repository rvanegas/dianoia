from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger

from .system_prompt import system_welcome_prompt, system_development_prompt
from core.utils import logger
from models.argument import argument_response_format, thesis_response_format, proofreadResponse

router = APIRouter()
client = OpenAI(api_key=OPENAI_API_KEY)

class Prompt(BaseModel):
    history: object = {}

@router.post("/chat")
async def chat(prompt: Prompt):
    welcome = True
    response_format=thesis_response_format
    messages = [{
        "role": "system",
        "content": system_welcome_prompt
    }] + prompt.history[:1]
    if len(prompt.history) > 2:
        welcome = False
        messages += [{
            "role": "system",
            "content": system_development_prompt
        }] + prompt.history[1:]
        response_format=argument_response_format

    logger.debug(f"messages {len(messages)}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=response_format,
    )
    content = response.choices[0].message.content

    if not welcome:
        errors = proofreadResponse(messages, prompt, content)
        if errors:
            logger.debug(f"errors: {errors}")

    return {"reply": content}
