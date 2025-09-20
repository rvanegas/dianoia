from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config import OPENAI_API_KEY
from core.utils import logger

from models import Conversation
from db.session import session
# session.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

class Prompt(BaseModel):
    prompt: str
    history: object = {}

class Step(BaseModel):
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
              "proposition": {
                "type": "string"
              },
              "justifier": {
                "type": "string"
              }
            },
            "required": ["proposition", "justifier"],
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

@app.post("/api/chat")
async def chat(prompt: Prompt):
    messages = [{
        "role": "system",
        "content": "You are a helpful assistant. Respond with JSON."
    }] + prompt.history
    logger.debug(f"messages {len(messages)}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format=response_format,
    )
    return {"reply": response.choices[0].message.content}
