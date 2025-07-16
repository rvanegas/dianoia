from fastapi import APIRouter, File, UploadFile

from core.utils import logger
from models.argument import (ArgumentsWithStep, ArgumentsWithProposition, ArgumentsWithStepAndProposition)
from services.assistant import FileData, create_file

router = APIRouter()

@router.post('/theses')
async def theses(args: ArgumentsWithProposition):
    new_args = args.theses()
    return {"reply": new_args}

@router.post("/assume")
async def evaluate(args: ArgumentsWithStep):
    new_args = args.assume()
    return {"reply": new_args}

@router.post("/remove")
async def remove(args: ArgumentsWithStep):
    new_args = args.remove()
    return {"reply": new_args}

@router.post("/ai-justify")
async def ai_justify(args: ArgumentsWithStep):
    new_args = args.ai_justify()
    return {"reply": new_args}

@router.post("/user-justify")
async def user_justify(args: ArgumentsWithStepAndProposition):
    new_args = args.user_justify()
    return {"reply": new_args}

@router.post("/explain")
async def user_justify(args: ArgumentsWithStep):
    new_args, explanation = args.explain()
    return {"reply": new_args, "explanation": explanation}

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    file_data = FileData(
        content=content,
        filename=file.filename)
    file_ref = create_file(file_data)
    return {"reply": file_ref}
