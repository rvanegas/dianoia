from fastapi import APIRouter

from core.utils import logger
from services.conversation import develop_argument, develop_theses, Prompt, ThesesPrompt

router = APIRouter()

@router.post("/chat")
async def chat(prompt: Prompt):
    content = develop_argument(prompt)
    return {"reply": content}

@router.post('/theses')
async def theses(thesesPrompt: ThesesPrompt):
    content = develop_theses(thesesPrompt)
    return {"reply": content}
