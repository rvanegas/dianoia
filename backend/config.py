"""env variables"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
DATABASE_URL = os.getenv("DATABASE_URL")
