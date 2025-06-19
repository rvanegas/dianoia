from fastapi import APIRouter

from core.utils import logger
from services.conversation import develop_argument, Prompt

router = APIRouter()

@router.post("/chat")
async def chat(prompt: Prompt):
    content = develop_argument(prompt)
    return {"reply": content}
