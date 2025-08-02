from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from services.agent_coordinator import coordinator

router = APIRouter()


class AgentTaskRequest(BaseModel):
    session_id: str
    conversation_id: int
    agent_type: str  # 'builder', 'evaluator', 'formalizer'
    data: Dict[str, Any]
    priority: int = 0


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/trigger")
async def trigger_agent_task(request: AgentTaskRequest) -> AgentTaskResponse:
    """Trigger a background agent task"""
    
    # Validate agent type
    valid_agent_types = ['builder', 'evaluator', 'formalizer']
    if request.agent_type not in valid_agent_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid agent_type. Must be one of: {valid_agent_types}"
        )
    
    # Construct conversation identifier
    conversation_identifier = f"{request.session_id}:{request.conversation_id}"
    
    # Queue the task
    task_id = coordinator.queue_task(
        agent_type=request.agent_type,
        conversation_id=conversation_identifier,
        data=request.data,
        priority=request.priority
    )
    
    return AgentTaskResponse(
        task_id=task_id,
        status="queued",
        message=f"Task queued for {request.agent_type} agent"
    )


@router.get("/status/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get the status of a specific task"""
    task = coordinator.get_task_status(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.id,
        "agent_type": task.agent_type,
        "status": task.status,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        "result": task.result,
        "error": task.error
    }


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
    
    return {
        "conversation_id": conversation_id,
        "results_by_agent": results_by_agent,
        "total_count": len(all_results),
        "agent_types": list(results_by_agent.keys())
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