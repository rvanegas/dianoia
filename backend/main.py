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
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)

class Prompt(BaseModel):
    prompt: str
    history: object = {}

@app.post("/api/chat")
async def chat(prompt: Prompt):
    messages = [{"role": "system", "content": "You are a helpful assistant."}] + prompt.history
    logger.debug(f"messages {len(messages)}")
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages
    )
    return {"reply": response.choices[0].message.content}
