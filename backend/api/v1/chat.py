from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger

from .system_prompt import system_prompt
from models.argument import response_format, ArgumentResponse

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
    return {"reply": content}
