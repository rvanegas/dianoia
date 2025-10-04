from fastapi import APIRouter

from core.utils import logger
from services.conversation import develop_argument, develop_theses
from models.argument import ArgumentPrompt, ThesesPrompt

router = APIRouter()

@router.post('/theses')
async def theses(thesesPrompt: ThesesPrompt):
    theses = develop_theses(thesesPrompt)
    return {"reply": theses}

@router.post("/argument")
async def argument(argumentPrompt: ArgumentPrompt):
    args, errors = develop_argument(argumentPrompt)
    return {"reply": args, "errors": errors}
