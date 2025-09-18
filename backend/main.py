from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

import os
import logging

load_dotenv()

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)  # or INFO, WARNING, etc.
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    # col1 = Column(String, nullable=False)
    # col2 = Column(String, unique=True, nullable=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# user = session.query(User).filter_by(name="Alice").first()
# print(user.email)
# session.close()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Prompt(BaseModel):
    prompt: str
    history: object = {}

@app.post("/api/chat")
async def chat(prompt: Prompt):
    messages = [{"role": "system", "content": "You are a helpful assistant."}] + prompt.history
    # logger.debug(f"messages {messages}")
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=messages
    )
    return {"reply": response.choices[0].message.content}
