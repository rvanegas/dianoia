from fastapi import APIRouter

from core.utils import logger
from models.argument import ArgumentsPrompt, ThesesPrompt, JustifyPrompt

router = APIRouter()

@router.post('/theses')
async def theses(prompt: ThesesPrompt):
    theses = prompt.develop()
    return {"reply": theses}

@router.post("/arguments")
async def arguments(prompt: ArgumentsPrompt):
    args, errors = prompt.develop()
    return {"reply": args, "errors": errors}

@router.post("/justify")
async def justify(prompt: JustifyPrompt):
    args = prompt.justify()
    return {"reply": args}
