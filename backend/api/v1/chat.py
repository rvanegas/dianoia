from fastapi import APIRouter, File, UploadFile

from core.utils import logger
from models.argument import (Theses,
    ArgumentsWithStep, ArgumentsWithProposition)
from models.file import FileData, create_file

router = APIRouter()

@router.post('/theses')
async def theses(theses: Theses):
    new_theses = theses.develop()
    return {"reply": new_theses}

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
    new_args = args.justify()
    return {"reply": new_args}

@router.post("/user-justify")
async def user_justify(args: ArgumentsWithProposition):
    new_args = args.user_justify()
    return {"reply": new_args}

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    file_data = FileData(
        content=content,
        filename=file.filename)
    create_file(file_data)
    return {"reply": file.filename}
