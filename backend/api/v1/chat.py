from fastapi import APIRouter

from core.utils import logger
from models.argument import (ThesesPrompt, Arguments,
    ArgumentsWithStepPrompt, ArgumentsWithPrompt)

router = APIRouter()

@router.post('/theses')
async def theses(prompt: ThesesPrompt):
    theses = prompt.develop()
    return {"reply": theses}

@router.post("/ai-justify")
async def justify(prompt: ArgumentsWithStepPrompt):
    args = prompt.justify()
    return {"reply": args}

@router.post("/remove")
async def remove(prompt: ArgumentsWithStepPrompt):
    args = prompt.remove()
    return {"reply": args}

@router.post("/evaluate")
async def evaluate(prompt: Arguments):
    args = prompt.evaluate()
    return {"reply": args}

@router.post("/user-justify")
async def user_justify(prompt: ArgumentsWithPrompt):
    args = prompt.user_justify()
    return {"reply": args}
