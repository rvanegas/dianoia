"""
Normalized Agent Input Schema for the rearchitected agent system.
This standardizes how all agents receive and process input data.
"""

from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
from schemas.step import Step


class AgentData(BaseModel):
    """Data that agents actually use for processing"""
    argument: List[Step]
    latest_results: List[Dict[str, Any]] = []  # Latest agent results for context
    target_type: Literal["argument", "proposition"]
    target_content: Optional[str] = None  # proposition text if target_type is 'proposition'


class AgentInput(BaseModel):
    """Complete input schema for agent coordination"""
    # Identifiers (needed for system operation)
    conversation_id: str
    snapshot_id: str  # Required - no default value
    
    # Agent data (what gets passed to the agent)
    agent_data: AgentData
    
    # Metadata (system-level info, not used by agents)
    file_ids: List[str] = []
    triggered_by: Literal["user_action", "agent_cascade", "scheduled", "manual"] = "user_action"
    trigger_source: str = ""
    

class FilteredAgentInput(AgentInput):
    """Agent input with content filtered based on agent type"""
    
    @classmethod
    def for_truth_evaluation(cls, base_input: AgentInput) -> "FilteredAgentInput":
        """Create input for truth evaluation agent (no formalization data, no justifiers)"""
        filtered_input = cls.model_validate(base_input.model_dump())
        for step in filtered_input.agent_data.argument:
            step.formalization = None
            step.justifiers = []
        return filtered_input

    @classmethod
    def for_content_validity_evaluation(cls, base_input: AgentInput) -> "FilteredAgentInput":
        """Create input for content validity evaluation agent (no formalization data)"""
        filtered_input = cls.model_validate(base_input.model_dump())
        for step in filtered_input.agent_data.argument:
            step.formalization = None
        return filtered_input

    @classmethod
    def for_formal_evaluation(cls, base_input: AgentInput) -> "FilteredAgentInput":
        """Create input for formal evaluation agent (no content data)"""
        # Create a deep copy of the base input as FilteredAgentInput
        filtered_input = cls.model_validate(base_input.model_dump())
        
        # Filter out content data for formal evaluation by setting to empty string
        for step in filtered_input.agent_data.argument:
            step.proposition = ""

        return filtered_input
    
    @classmethod
    def for_formalization(cls, base_input: AgentInput) -> "FilteredAgentInput":
        """Create input for formalization agent (includes all data for context)"""
        # Create a deep copy of the base input as FilteredAgentInput
        filtered_input = cls.model_validate(base_input.model_dump())
        
        # Keep all data for formalization context
        # The formalization agent needs to see existing formalizations for consistency
        return filtered_input
