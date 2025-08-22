from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any

from services.agent_coordinator import coordinator
from services.agents import FormalEvaluatorAgent
from schemas.arguments import Arguments
from core.utils import logger
# import time

router = APIRouter()

@router.get("/results")
async def get_conversation_results(
    conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)"),
    snapshot_id: str = Query(..., description="Snapshot ID for filtering results")
) -> Dict[str, Any]:
    """Get latest agent results for a conversation/snapshot, grouped by agent type"""
    return coordinator.result_manager.get_formatted_results(conversation_id, snapshot_id)

@router.post("/evaluate-form")
async def trigger_formal_evaluation(
    args: Arguments,
    conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)"),
    snapshot_id: str = Query(..., description="Snapshot ID for agent coordination")
) -> Dict[str, Any]:
    """Trigger formal evaluation agent for endorsed formalizations"""
    try:
        # Set conversation_id on args
        args.conversation_id = conversation_id
        
        # Validate and queue formal evaluation task
        agent = FormalEvaluatorAgent(coordinator)
        validation_result = agent.validate_formalizations(args)
        
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=400, 
                detail=validation_result["error_message"]
            )
        
        return agent.create_and_queue_formal_evaluation_task(conversation_id, snapshot_id, args)
        
    except Exception as e:
        logger.error(f"Error triggering formal evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_tasks(conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)")) -> Dict[str, Any]:
    """Get all currently active tasks for a specific conversation"""
    return coordinator.result_manager.get_active_tasks_formatted(conversation_id) 
