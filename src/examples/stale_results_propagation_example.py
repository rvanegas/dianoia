#!/usr/bin/env python3
"""
Example demonstrating the StaleResultsPropagation system.

This example shows how to:
1. Get latest results for a conversation/snapshot context
2. Create agent input with latest results context
3. Create properly structured agent results
4. Filter results by target type
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from services.agent_coordinator import coordinator, StoredAgentResult, TargetMetadata
from schemas.agent_input import AgentData
from schemas.arguments import Step


def main():
    """Demonstrate the StaleResultsPropagation system"""
    print("=== StaleResultsPropagation System Example ===\n")
    
    conversation_id = "example_conversation_123"
    
    # Step 1: Add some example results with different snapshots
    print("1. Adding example results with different snapshots...")
    
    # Snapshot 1: Initial formalization
    formalization_1 = coordinator.create_agent_result(
        agent_type='formalizer',
        operation='formalize_proposition',
        result_content={'proposition': 'Socrates is a man', 'ascii': 'P(a)'},
        confidence=0.9,
        reasoning='Formalized basic proposition',
        target_metadata=TargetMetadata(target_type='proposition', target_content='Socrates is a man'),
        snapshot_id='1'
    )
    coordinator.result_manager.add_result(conversation_id, formalization_1)
    
    # Snapshot 2: Content evaluation
    content_eval = coordinator.create_agent_result(
        agent_type='content_evaluator',
        operation='evaluate_propositions',
        result_content={
            'evaluation': {
                'proposition_evaluations': [
                    {'proposition': 'Socrates is a man', 'truth_value': 0.95}
                ],
                'argument_validity': 0.95
            }
        },
        confidence=0.95,
        reasoning='Evaluated proposition truth value',
        target_metadata=TargetMetadata(target_type='argument', target_content=''),
        snapshot_id='2'
    )
    coordinator.result_manager.add_result(conversation_id, content_eval)
    
    # Snapshot 3: Updated formalization
    formalization_2 = coordinator.create_agent_result(
        agent_type='formalizer',
        operation='formalize_proposition',
        result_content={'proposition': 'Socrates is a man', 'ascii': 'P(socrates)'},
        confidence=0.95,
        reasoning='Improved formalization with proper naming',
        target_metadata=TargetMetadata(target_type='proposition', target_content='Socrates is a man'),
        snapshot_id='3'
    )
    coordinator.result_manager.add_result(conversation_id, formalization_2)
    
    print(f"   Added 3 results across snapshots 1, 2, and 3\n")
    
    # Step 2: Demonstrate getting latest results
    print("2. Getting latest results...")
    
    # Get all latest results
    latest_results = coordinator.get_latest_results(conversation_id, '3')
    print(f"   Latest results (all snapshots): {len(latest_results)} results")
    for result in latest_results:
        print(f"   - {result.agent_type}: {result.result_content}")
    
    # Get results up to snapshot 2
    results_snapshot_2 = coordinator.get_latest_results(conversation_id, '2')
    print(f"\n   Latest results (up to snapshot 2): {len(results_snapshot_2)} results")
    for result in results_snapshot_2:
        print(f"   - {result.agent_type}: {result.result_content}")
    
    print()
    
    # Step 3: Demonstrate filtering by target type
    print("3. Filtering results by target type...")
    
    # Get argument-level results
    argument_results = coordinator.get_results_by_target_type(conversation_id, 'argument', '3')
    print(f"   Argument-level results: {len(argument_results)} results")
    for result in argument_results:
        print(f"   - {result.agent_type}: {result.result_content}")
    
    # Get proposition-level results
    proposition_results = coordinator.get_results_by_target_type(conversation_id, 'proposition', '3')
    print(f"   Proposition-level results: {len(proposition_results)} results")
    for result in proposition_results:
        print(f"   - {result.agent_type}: {result.result_content}")
    
    print()
    
    # Step 4: Demonstrate creating agent input with context
    print("4. Creating agent input with latest results context...")
    
    # Create agent data for a new task
    agent_data = AgentData(
        argument=[],
        latest_results=[],  # Will be populated by create_agent_input
        target_type='proposition',
        target_content='All men are mortal'
    )
    
    # Create agent input with context from latest results
    agent_input = coordinator.create_agent_input(
        conversation_id=conversation_id,
        snapshot_id='4',  # New snapshot
        agent_data=agent_data,
        file_ids=['example.txt'],
        triggered_by='user_action',
        trigger_source='argument_change'
    )
    
    print(f"   Created agent input for snapshot 4")
    print(f"   Context includes {len(agent_input.agent_data.latest_results)} previous results")
    print(f"   Latest results context:")
    for result in agent_input.agent_data.latest_results:
        print(f"   - {result['agent_type']}: {result['result_content']}")
    
    print()
    
    # Step 5: Demonstrate creating a new result
    print("5. Creating a new agent result...")
    
    new_result = coordinator.create_agent_result(
        agent_type='formalizer',
        operation='formalize_proposition',
        result_content={'proposition': 'All men are mortal', 'ascii': 'forall x. (Man(x) -> Mortal(x))'},
        confidence=0.9,
        reasoning='Formalized universal proposition',
        target_metadata=TargetMetadata(target_type='proposition', target_content='All men are mortal'),
        snapshot_id='4'
    )
    
    print(f"   Created new result: {new_result.agent_type}")
    print(f"   Content: {new_result.result_content}")
    print(f"   Target: {new_result.target_metadata.target_type} - {new_result.target_metadata.target_content}")
    
    print("\n=== Example Complete ===")


if __name__ == "__main__":
    main()
