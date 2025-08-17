from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Depends

from core.utils import logger
from schemas.arguments import (
    Arguments,
    ArgumentsWithStep,
    ArgumentsWithProposition,
    ArgumentsWithStepAndProposition)
from services.argument_service import (
    ArgumentService,
    ArgumentStepService,
    ArgumentPropositionService,
    ArgumentStepAndPropositionService)
from services.file import FileData, create_file

router = APIRouter()

def get_conversation_handler(operation_name: str):
    """Dependency that returns a conversation handler function"""
    def handler(session_id: str = Query(..., description="Session UUID"),
            conversation_id: int = Query(..., description="Conversation ID")):
        def conversation_handler(args):
            try:
                conversation_identifier = f"{session_id}:{conversation_id}"
                args.conversation_id = conversation_identifier
                # logger.info(f"{operation_name} operation for conversation: {conversation_identifier}")
                return args
            except Exception as e:
                logger.error(f"{operation_name} error: {e}")
                raise HTTPException(status_code=422, detail=str(e))
        return conversation_handler
    return handler

@router.post('/argue')
async def argue(args: ArgumentsWithProposition,
        handler = Depends(get_conversation_handler("Argue"))):
    args = handler(args)
    service = ArgumentPropositionService(args)
    result = service.argue()
    return {"reply": result}

@router.post('/gen-name')
async def gen_name(args: ArgumentsWithProposition,
        handler = Depends(get_conversation_handler("gen_name"))):
    args = handler(args)
    service = ArgumentPropositionService(args)
    result = service.gen_name()
    return {"reply": result}

@router.post("/assume")
async def assume(args: ArgumentsWithStep,
        handler = Depends(get_conversation_handler("Assume"))):
    args = handler(args)
    service = ArgumentStepService(args)
    result = service.assume()
    return {"reply": result}

@router.post("/remove")
async def remove(args: ArgumentsWithStep,
        handler = Depends(get_conversation_handler("Remove"))):
    args = handler(args)
    service = ArgumentStepService(args)
    result = service.remove()
    return {"reply": result}

@router.post("/ai-justify")
async def ai_justify(args: ArgumentsWithStep,
        handler = Depends(get_conversation_handler("AI justify"))):
    args = handler(args)
    service = ArgumentStepService(args)
    result = service.ai_justify()
    return {"reply": result}

@router.post("/user-justify")
async def user_justify(args: ArgumentsWithStepAndProposition,
        handler = Depends(get_conversation_handler("User justify"))):
    args = handler(args)
    service = ArgumentStepAndPropositionService(args)
    result = service.user_justify()
    return {"reply": result}

@router.post("/explain")
async def explain(args: ArgumentsWithStep,
        handler = Depends(get_conversation_handler("Explain"))):
    args = handler(args)
    service = ArgumentStepService(args)
    result = service.explain()
    return {"reply": result}

@router.post("/evaluate")
async def evaluate(args: Arguments,
        handler = Depends(get_conversation_handler("Evaluate"))):
    args = handler(args)
    service = ArgumentService(args)
    result = service.evaluate()
    return {"reply": result}

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    file_data = FileData(
        content=content,
        filename=file.filename)
    file_ref = create_file(file_data)
    return {"reply": file_ref}
