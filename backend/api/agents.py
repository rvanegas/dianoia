from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from services.agent_coordinator import coordinator
# from models.argument import Arguments
from core.utils import logger
# import time

router = APIRouter()

@router.get("/results/{conversation_id}")
async def get_conversation_results(conversation_id: str) -> Dict[str, Any]:
    """Get all agent results for a conversation, grouped by agent type"""
    all_results = coordinator.get_conversation_results(conversation_id)
    
    # Group results by agent type
    results_by_agent = {}
    for result in all_results:
        agent_type = result.get('agent_type', 'unknown')
        if agent_type not in results_by_agent:
            results_by_agent[agent_type] = []
        results_by_agent[agent_type].append(result)
    
    # Check if all tasks for this conversation are complete
    tasks_complete = coordinator.are_conversation_tasks_complete(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "results_by_agent": results_by_agent,
        "total_count": len(all_results),
        "agent_types": list(results_by_agent.keys()),
        "tasks_complete": tasks_complete
    }

@router.get("/active")
async def get_active_tasks() -> Dict[str, Any]:
    """Get all currently active tasks"""
    active_tasks = coordinator.get_active_tasks()
    
    return {
        "active_tasks": [
            {
                "task_id": task.id,
                "agent_type": task.agent_type,
                "status": task.status,
                "conversation_id": task.conversation_id
            }
            for task in active_tasks
        ],
        "count": len(active_tasks)
    } 