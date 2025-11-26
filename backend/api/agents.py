from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any

from services.agent_coordinator import coordinator
# from models.argument import Arguments
from core.utils import logger
# import time

router = APIRouter()

@router.get("/results")
async def get_conversation_results(conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)")) -> Dict[str, Any]:
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
async def get_active_tasks(conversation_id: str = Query(..., description="Conversation ID (format: session_id:conversation_id)")) -> Dict[str, Any]:
    """Get all currently active tasks for a specific conversation"""
    active_tasks = coordinator.get_active_tasks()
    
    # Filter tasks by conversation_id
    filtered_tasks = [
        task for task in active_tasks 
        if task.conversation_id == conversation_id
    ]
    
    return {
        "active_tasks": [
            {
                "task_id": task.id,
                "agent_type": task.agent_type,
                "status": task.status,
                "conversation_id": task.conversation_id
            }
            for task in filtered_tasks
        ],
        "count": len(filtered_tasks)
    } 