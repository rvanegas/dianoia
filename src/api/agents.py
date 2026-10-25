from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any

from schemas.api_results import AgentResultsResponse
from services.agent_coordinator import coordinator


from core.utils import logger
# import time

router = APIRouter()

# Documented, not enforced: see schemas/api_results.py for why.
@router.get("/results", response_model=None, responses={200: {"model": AgentResultsResponse}})
async def get_conversation_results(
    conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)"),
    snapshot_id: str = Query(..., description="Snapshot ID for filtering results")
) -> Dict[str, Any]:
    """Get latest agent results for a conversation/snapshot, grouped by agent type"""
    # logger.info(f"🔤 API: Getting results for conversation {conversation_id}, snapshot {snapshot_id}")
    result = coordinator.result_manager.get_formatted_results(conversation_id, snapshot_id, coordinator)
    # logger.info(f"🔤 API: Conversation name in response: {result.get('conversation_name', 'None')}")
    return result

@router.get("/active")
async def get_active_tasks(conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)")) -> Dict[str, Any]:
    """Get all currently active tasks for a specific conversation"""
    return coordinator.result_manager.get_active_tasks_formatted(conversation_id, coordinator) 
