from fastapi import APIRouter

from core.utils import logger
from services.conversation import develop_argument, develop_theses
from models.argument import ArgumentPrompt, ThesesPrompt

router = APIRouter()

@router.post("/argument")
async def chat(argumentPrompt: ArgumentPrompt):
    content = develop_argument(argumentPrompt)
    return {"reply": content}

@router.post('/theses')
async def theses(thesesPrompt: ThesesPrompt):
    content = develop_theses(thesesPrompt)
    return {"reply": content}
