from fastapi import APIRouter

from core.utils import logger
from models.argument import ArgumentPrompt, ThesesPrompt, JustifyPrompt

router = APIRouter()

@router.post('/theses')
async def theses(prompt: ThesesPrompt):
    theses = prompt.develop()
    return {"reply": theses}

@router.post("/argument")
async def argument(prompt: ArgumentPrompt):
    args, errors = prompt.develop()
    return {"reply": args, "errors": errors}

@router.post("/justify")
async def justify(prompt: JustifyPrompt):
    new_args = prompt.justify()
    return {"reply": new_args}
