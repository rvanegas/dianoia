from fastapi import APIRouter

from core.utils import logger
from services.conversation import develop_argument, develop_thesis, Prompt

router = APIRouter()

@router.post("/chat")
async def chat(prompt: Prompt):
    content = develop_argument(prompt)
    return {"reply": content}

@router.post('/thesis')
async def thesis():
    content = develop_thesis()
    return {"reply": content}
