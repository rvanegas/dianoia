"""
Normalized Agent Input Schema for the rearchitected agent system.
This standardizes how all agents receive and process input data.
"""

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
from schemas.step import Step


class AgentContext(BaseModel):
    """Context data provided to all agents"""
    assumptions: List[Step]
    argument: List[Step]
    file_ids: List[str] = []


class TaskData(BaseModel):
    """Task-specific data for agent processing"""
    target_type: Literal["argument", "proposition"]
    target_content: Optional[str] = None  # proposition text if target_type is 'proposition'


class AgentMetadata(BaseModel):
    """Metadata about the agent task"""
    triggered_by: Literal["user_action", "agent_cascade", "scheduled", "manual"]
    trigger_source: str


class AgentInput(BaseModel):
    """Normalized input schema for all agents"""
    # Core identification
    conversation_id: str
    snapshot_id: str
    
    # Context data
    context: AgentContext
    
    # Task-specific data
    task_data: TaskData
    
    # Metadata
    metadata: AgentMetadata


class FilteredAgentInput(AgentInput):
    """Agent input with content filtered based on agent type"""
    
    @classmethod
    def for_content_evaluation(cls, base_input: AgentInput) -> "FilteredAgentInput":
        """Create input for content evaluation agent (no formalization data)"""
        # Create a deep copy of the base input as FilteredAgentInput
        filtered_input = cls.model_validate(base_input.model_dump())
        
        # Filter out formalization data for content evaluation
        for step in filtered_input.context.assumptions:
            step.formalization = None
        for step in filtered_input.context.argument:
            step.formalization = None
        
        return filtered_input
    
    @classmethod
    def for_formal_evaluation(cls, base_input: AgentInput) -> "FilteredAgentInput":
        """Create input for formal evaluation agent (no content data)"""
        # Create a deep copy of the base input as FilteredAgentInput
        filtered_input = cls.model_validate(base_input.model_dump())
        
        # Filter out content data for formal evaluation
        for step in filtered_input.context.assumptions:
            step.proposition = None
        for step in filtered_input.context.argument:
            step.proposition = None
        
        return filtered_input
