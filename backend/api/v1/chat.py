from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger

from .system_prompt import system_prompt
from core.utils import logger
from models.argument import response_format, Response, proofreadResponse

router = APIRouter()
client = OpenAI(api_key=OPENAI_API_KEY)

class Prompt(BaseModel):
    history: object = {}

@router.post("/chat")
async def chat(prompt: Prompt):
    messages = [{
        "role": "system",
        "content": system_prompt
    }] + prompt.history
    logger.debug(f"messages {len(messages)}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=response_format,
    )
    content = response.choices[0].message.content
    response = Response.parse_raw(content)
    prev_responses = [m for m in messages if m["role"] == "assistant"]
    prev_response = prev_responses[-1] if prev_responses else None
    if prev_response:
        errors = proofreadResponse(prev_response, response)
        if errors:
            logger.debug("errors:")
            logger.debug(errors)
    return {"reply": content}
