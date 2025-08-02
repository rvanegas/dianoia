from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from functools import wraps
from uuid import UUID

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

def handle_argument_operation(operation_name: str):
    """Decorator to handle conversation identification, logging, and assistant errors"""
    def decorator(func):
        @wraps(func)
        async def wrapper(args, session_id: str = Query(..., description="Session UUID"),
                         conversation_id: int = Query(..., description="Conversation ID"),
                         **kwargs):
            try:
                # Handle conversation identification
                conversation_identifier = f"{session_id}:{conversation_id}"
                args.conversation_id = conversation_identifier
                logger.info(f"{operation_name} operation for conversation: {conversation_identifier}")
                
                # Execute the original function
                result = await func(args, **kwargs)
                return {"reply": result}
            except AssistantResponseError as e:
                logger.error(f"{operation_name} error: {e}")
                raise HTTPException(status_code=422, detail=str(e))
        return wrapper
    return decorator

@router.post('/theses')
@handle_argument_operation("Theses")
async def theses(args: ArgumentsWithProposition):
    return args.theses()

@router.post('/argue')
@handle_argument_operation("Argue")
async def argue(args: ArgumentsWithLoc):
    return args.argue()

@router.post("/assume")
@handle_argument_operation("Assume")
async def assume(args: ArgumentsWithStep):
    return args.assume()

@router.post("/remove")
@handle_argument_operation("Remove")
async def remove(args: ArgumentsWithStep):
    return args.remove()

@router.post("/ai-justify")
@handle_argument_operation("AI justify")
async def ai_justify(args: ArgumentsWithStep):
    return args.ai_justify()

@router.post("/user-justify")
@handle_argument_operation("User justify")
async def user_justify(args: ArgumentsWithStepAndProposition):
    return args.user_justify()

@router.post("/explain")
@handle_argument_operation("Explain")
async def explain(args: ArgumentsWithStep):
    return args.explain()

@router.post("/evaluate")
@handle_argument_operation("Evaluate")
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
