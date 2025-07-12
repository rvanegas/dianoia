from fastapi import APIRouter

from core.utils import logger
from models.argument import (ThesesPrompt,
    ArgumentsWithStep, ArgumentsWithProposition)

router = APIRouter()

@router.post('/theses')
async def theses(prompt: ThesesPrompt):
    theses = prompt.develop()
    return {"reply": theses}

@router.post("/assume")
async def evaluate(prompt: ArgumentsWithStep):
    args = prompt.assume()
    return {"reply": args}

@router.post("/remove")
async def remove(prompt: ArgumentsWithStep):
    args = prompt.remove()
    return {"reply": args}

@router.post("/ai-justify")
async def justify(prompt: ArgumentsWithStep):
    args = prompt.justify()
    return {"reply": args}

@router.post("/user-justify")
async def user_justify(prompt: ArgumentsWithProposition):
    args = prompt.user_justify()
    return {"reply": args}
