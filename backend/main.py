from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger("myapp")
logger.setLevel(logging.DEBUG)  # or INFO, WARNING, etc.
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

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
    history: str = ""

@app.post("/api/chat")
async def chat(prompt: Prompt):
    logger.debug(f"prompt {prompt}")
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt.prompt}
        ]
    )
    return {"reply": response.choices[0].message.content}

