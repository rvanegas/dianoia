from fastapi import APIRouter

from core.utils import logger
from services.conversation import (develop_argument, develop_theses,
    justify_proposition)
from models.argument import ArgumentPrompt, ThesesPrompt, JustifyPrompt

router = APIRouter()

@router.post('/theses')
async def theses(thesesPrompt: ThesesPrompt):
    theses = develop_theses(thesesPrompt)
    return {"reply": theses}

@router.post("/argument")
async def argument(argumentPrompt: ArgumentPrompt):
    args, errors = develop_argument(argumentPrompt)
    return {"reply": args, "errors": errors}

@router.post("/justify")
async def justify(justifyPrompt: JustifyPrompt):
    new_args, errors = justify_proposition(justifyPrompt)
    return {"reply": new_args, "errors": errors}
