from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from config import OPENAI_API_KEY
from core.utils import logger

router = APIRouter()
client = OpenAI(api_key=OPENAI_API_KEY)

class Prompt(BaseModel):
    history: object = {}

class Step(BaseModel):
    index: int
    proposition: str
    justifier: str

class Response(BaseModel):
    argument: list[Step]
    explanation: str

response_format = {
  "type": "json_schema",
  "json_schema": {
    "name": "response",
    "strict": True,
    "schema": {
      "type": "object",
      "properties": {
        "argument": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "index": {
                "type": "integer"
              },
              "proposition": {
                "type": "string"
              },
              "justifier": {
                "type": "string"
              }
            },
            "required": ["index", "proposition", "justifier"],
            "additionalProperties": False
          }
        },
        "explanation": {
          "type": "string"
        }
      },
      "required": ["argument", "explanation"],
      "additionalProperties": False
    }
  }
}

with open('api/v1/system_prompt.txt', 'r') as file:
    system_prompt = file.read()

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
    return {"reply": response.choices[0].message.content}
