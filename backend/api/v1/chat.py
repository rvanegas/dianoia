from fastapi import APIRouter

from core.utils import logger
from models.argument import (
    Arguments, ArgumentsPrompt,
    ThesesPrompt, ArgumentsWithStepPrompt)

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
