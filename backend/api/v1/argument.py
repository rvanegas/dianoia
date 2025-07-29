from fastapi import APIRouter, File, UploadFile, HTTPException
from functools import wraps

from core.utils import logger
from models.argument import (
    Arguments,
    ArgumentsWithLoc,
    ArgumentsWithStep,
    ArgumentsWithProposition,
    ArgumentsWithStepAndProposition)
from services.file import FileData, create_file
from services.conversation import AssistantResponseError

router = APIRouter()

def handle_assistant_errors(operation_name: str):
    """Decorator to handle AssistantResponseError consistently across endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return {"reply": result}
            except AssistantResponseError as e:
                logger.error(f"{operation_name} error: {e}")
                raise HTTPException(status_code=422, detail=str(e))
        return wrapper
    return decorator

@router.post('/theses')
@handle_assistant_errors("Theses")
async def theses(args: ArgumentsWithProposition):
    return args.theses()

@router.post('/argue')
@handle_assistant_errors("Argue")
async def argue(args: ArgumentsWithLoc):
    return args.argue()

@router.post("/assume")
@handle_assistant_errors("Assume")
async def assume(args: ArgumentsWithStep):
    return args.assume()

@router.post("/remove")
@handle_assistant_errors("Remove")
async def remove(args: ArgumentsWithStep):
    return args.remove()

@router.post("/ai-justify")
@handle_assistant_errors("AI justify")
async def ai_justify(args: ArgumentsWithStep):
    return args.ai_justify()

@router.post("/user-justify")
@handle_assistant_errors("User justify")
async def user_justify(args: ArgumentsWithStepAndProposition):
    return args.user_justify()

@router.post("/explain")
@handle_assistant_errors("Explain")
async def explain(args: ArgumentsWithStep):
    return args.explain()

@router.post("/evaluate")
@handle_assistant_errors("Evaluate")
async def evaluate(args: Arguments):
    return args.evaluate()

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    file_data = FileData(
        content=content,
        filename=file.filename)
    file_ref = create_file(file_data)
    return {"reply": file_ref}
