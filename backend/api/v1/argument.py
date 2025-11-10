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

@router.post('/theses')
async def theses(args: ArgumentsWithProposition, 
                session_id: str = Query(..., description="Session UUID"),
                conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"Theses operation for conversation: {conversation_identifier}")
        result = args.theses()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"Theses error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post('/argue')
async def argue(args: ArgumentsWithLoc, 
               session_id: str = Query(..., description="Session UUID"),
               conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"Argue operation for conversation: {conversation_identifier}")
        result = args.argue()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"Argue error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/assume")
async def assume(args: ArgumentsWithStep, 
                session_id: str = Query(..., description="Session UUID"),
                conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"Assume operation for conversation: {conversation_identifier}")
        result = args.assume()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"Assume error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/remove")
async def remove(args: ArgumentsWithStep, 
                session_id: str = Query(..., description="Session UUID"),
                conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"Remove operation for conversation: {conversation_identifier}")
        result = args.remove()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"Remove error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/ai-justify")
async def ai_justify(args: ArgumentsWithStep, 
                    session_id: str = Query(..., description="Session UUID"),
                    conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"AI justify operation for conversation: {conversation_identifier}")
        result = args.ai_justify()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"AI justify error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/user-justify")
async def user_justify(args: ArgumentsWithStepAndProposition, 
                      session_id: str = Query(..., description="Session UUID"),
                      conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"User justify operation for conversation: {conversation_identifier}")
        result = args.user_justify()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"User justify error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/explain")
async def explain(args: ArgumentsWithStep, 
                session_id: str = Query(..., description="Session UUID"),
                conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"Explain operation for conversation: {conversation_identifier}")
        result = args.explain()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"Explain error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/evaluate")
async def evaluate(args: Arguments, 
                 session_id: str = Query(..., description="Session UUID"),
                 conversation_id: int = Query(..., description="Conversation ID")):
    try:
        conversation_identifier = f"{session_id}:{conversation_id}"
        args.conversation_id = conversation_identifier
        logger.info(f"Evaluate operation for conversation: {conversation_identifier}")
        result = args.evaluate()
        return {"reply": result}
    except AssistantResponseError as e:
        logger.error(f"Evaluate error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    file_data = FileData(
        content=content,
        filename=file.filename)
    file_ref = create_file(file_data)
    return {"reply": file_ref}
