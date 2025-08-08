"""
Agent queuing functions to centralize agent task queuing logic.
This module avoids circular imports by being imported by both agents.py and argument.py.
"""

from typing import Dict, Any, List
from core.utils import logger


def queue_argument_state_change(coordinator, conversation_id: str, argument_data: Dict[str, Any], additional_data: Dict[str, Any] = None):
    """
    Queue agents for argument state changes.
    This centralizes all agent queuing logic for argument modifications.
    """
    additional_data = additional_data or {}
    
    # Extract argument propositions for analysis
    argument_propositions = [step['proposition'] for step in argument_data['argument']]
    
    # Queue content discovery (builder agent)
    discovery_task_data = {
        'argument_data': {
            'argument': argument_data['argument'],
            'counter_argument': argument_data['counter_argument'],
            'assumptions': argument_data['assumptions'],
            'thesis': argument_data['thesis'],
            'counter_thesis': argument_data['counter_thesis'],
            'presupposition': argument_data['presupposition']
        },
        **additional_data
    }
    coordinator.queue_task(
        agent_type='builder',
        conversation_id=conversation_id,
        data=discovery_task_data
    )
    
    # Queue formalizer for specific proposition if provided
    proposition = additional_data.get('proposition', '')
    if proposition:
        queue_formalizer_for_proposition(
            coordinator,
            conversation_id,
            proposition,
            discovery_task_data['argument_data'],
            argument_data['file_ids']
        )
    
    # Queue argument analysis (content evaluator)
    analysis_task_data = {
        'argument': argument_propositions,
        'thesis': argument_data['thesis'],
        'counter_thesis': argument_data['counter_thesis'],
        'assumptions': argument_data['assumptions'],
        'file_ids': argument_data['file_ids'],
        **additional_data
    }
    coordinator.queue_task(
        agent_type='content_evaluator',
        conversation_id=conversation_id,
        data=analysis_task_data
    )


def queue_formalizer_for_proposition(coordinator, conversation_id: str, proposition: str, argument_data: Dict[str, Any] = None, file_ids: List[str] = None):
    """
    Queue formalizer agent for a specific proposition.
    This centralizes formalizer queuing logic.
    """
    argument_data = argument_data or {}
    file_ids = file_ids or []
    
    # Get existing formalizations to avoid duplicate work
    existing_results = coordinator.get_conversation_results(conversation_id)
    formalized_propositions = set()
    for result in existing_results:
        if result.get('agent_type') == 'formalizer':
            existing_proposition = result.get('data', {}).get('proposition')
            if existing_proposition:
                formalized_propositions.add(existing_proposition)
    
    # Only queue formalizer task if this proposition hasn't been formalized yet
    if proposition not in formalized_propositions:
        logger.info(f"Queueing formalizer task for proposition: '{proposition[:50]}...'")
        
        task_data = {
            'proposition': proposition,
            'argument_data': argument_data,
            'file_ids': file_ids
        }
        
        coordinator.queue_task(
            agent_type='formalizer',
            conversation_id=conversation_id,
            data=task_data
        )
        
        logger.info(f"Queued formalizer task for proposition: {proposition}")
    else:
        logger.info(f"Proposition already formalized: {proposition}")
