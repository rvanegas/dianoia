import pytest
import time
from services.agent_coordinator import coordinator, AgentResultManager, StoredAgentResult, TargetMetadata
from schemas.agent_input import AgentInput, AgentData
from schemas.arguments import Step


class TestStaleResultsPropagation:
    """Test the StaleResultsPropagation system"""
    
    def test_get_latest_results_basic(self):
        """Test basic latest results retrieval"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add multiple results for the same agent type
        old_result = StoredAgentResult(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={'old': 'result'},
            confidence=0.5,
            reasoning='Old evaluation',
            target_metadata=TargetMetadata(target_type='argument', target_content=''),
            snapshot_id='1',
            processed_at=time.time() - 100  # Old timestamp
        )
        
        new_result = StoredAgentResult(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={'new': 'result'},
            confidence=0.9,
            reasoning='New evaluation',
            target_metadata=TargetMetadata(target_type='argument', target_content=''),
            snapshot_id='1',
            processed_at=time.time()  # New timestamp
        )
        
        result_manager.add_result(conversation_id, old_result)
        result_manager.add_result(conversation_id, new_result)
        
        # Should return only the latest result
        latest_results = result_manager.get_latest_results(conversation_id, '1')
        assert len(latest_results) == 1
        assert latest_results[0].result_content == {'new': 'result'}
    
    def test_get_latest_results_snapshot_filtering(self):
        """Test snapshot-aware result filtering"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add results with different snapshot IDs
        snapshot_1_result = StoredAgentResult(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'Test 1'},
            confidence=0.8,
            reasoning='Snapshot 1 formalization',
            target_metadata=TargetMetadata(target_type='proposition', target_content='Test 1'),
            snapshot_id='1',
            processed_at=time.time()
        )
        
        snapshot_2_result = StoredAgentResult(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'Test 2'},
            confidence=0.8,
            reasoning='Snapshot 2 formalization',
            target_metadata=TargetMetadata(target_type='proposition', target_content='Test 2'),
            snapshot_id='2',
            processed_at=time.time()
        )
        
        result_manager.add_result(conversation_id, snapshot_1_result)
        result_manager.add_result(conversation_id, snapshot_2_result)
        
        # Get results up to snapshot 1
        results_snapshot_1 = result_manager.get_latest_results(conversation_id, '1')
        assert len(results_snapshot_1) == 1
        assert results_snapshot_1[0].snapshot_id == '1'
        
        # Get results up to snapshot 2
        results_snapshot_2 = result_manager.get_latest_results(conversation_id, '2')
        assert len(results_snapshot_2) == 1
        assert results_snapshot_2[0].snapshot_id == '2'  # Latest result
    
    def test_get_results_by_target_type(self):
        """Test filtering results by target type"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add results with different target types
        argument_result = StoredAgentResult(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={'argument': 'evaluation'},
            confidence=0.8,
            reasoning='Argument evaluation',
            target_metadata=TargetMetadata(target_type='argument', target_content=''),
            snapshot_id='1',
            processed_at=time.time()
        )
        
        proposition_result = StoredAgentResult(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'formalization'},
            confidence=0.9,
            reasoning='Proposition formalization',
            target_metadata=TargetMetadata(target_type='proposition', target_content='Test prop'),
            snapshot_id='1',
            processed_at=time.time()
        )
        
        result_manager.add_result(conversation_id, argument_result)
        result_manager.add_result(conversation_id, proposition_result)
        
        # Filter by argument type
        argument_results = result_manager.get_results_by_target_type(conversation_id, 'argument', '1')
        assert len(argument_results) == 1
        assert argument_results[0].target_metadata.target_type == 'argument'
        
        # Filter by proposition type
        proposition_results = result_manager.get_results_by_target_type(conversation_id, 'proposition', '1')
        assert len(proposition_results) == 1
        assert proposition_results[0].target_metadata.target_type == 'proposition'
    
    def test_create_agent_input_with_context(self):
        """Test creating agent input with latest results context"""
        conversation_id = "test_conversation_context"
        snapshot_id = "2"
        
        # Add some existing results
        existing_result = StoredAgentResult(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'Existing formalization'},
            confidence=0.8,
            reasoning='Existing result',
            target_metadata=TargetMetadata(target_type='proposition', target_content='Existing'),
            snapshot_id='1',
            processed_at=time.time()
        )
        
        coordinator.result_manager.add_result(conversation_id, existing_result)
        
        # Create agent data
        agent_data = AgentData(
            assumptions=[],
            argument=[],
            latest_results=[],
            target_type='proposition',
            target_content='New proposition'
        )
        
        # Create agent input with context
        agent_input = coordinator.create_agent_input(
            conversation_id=conversation_id,
            snapshot_id=snapshot_id,
            agent_data=agent_data,
            file_ids=['file1.txt'],
            triggered_by='user_action',
            trigger_source='argument_change'
        )
        
        # Verify the agent input has the latest results context
        assert agent_input.conversation_id == conversation_id
        assert agent_input.snapshot_id == snapshot_id
        assert agent_input.file_ids == ['file1.txt']
        assert agent_input.triggered_by == 'user_action'
        assert agent_input.trigger_source == 'argument_change'
        assert len(agent_input.agent_data.latest_results) == 1
        assert agent_input.agent_data.latest_results[0]['agent_type'] == 'formalizer'
    
    def test_create_agent_result(self):
        """Test creating properly structured agent result"""
        target_metadata = TargetMetadata(target_type='proposition', target_content='Test proposition')
        
        result = coordinator.create_agent_result(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'Test formalization'},
            confidence=0.9,
            reasoning='Test reasoning',
            target_metadata=target_metadata,
            snapshot_id='1'
        )
        
        # Verify the result structure
        assert result.agent_type == 'formalizer'
        assert result.operation == 'formalize_proposition'
        assert result.result_content == {'proposition': 'Test formalization'}
        assert result.confidence == 0.9
        assert result.reasoning == 'Test reasoning'
        assert result.target_metadata == target_metadata
        assert result.snapshot_id == '1'
        assert result.processed_at > 0
    
    def test_coordinator_get_latest_results(self):
        """Test coordinator's get_latest_results method"""
        conversation_id = "test_conversation_coordinator"
        
        # Add a result through the coordinator
        target_metadata = TargetMetadata(target_type='argument', target_content='')
        result = coordinator.create_agent_result(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={'evaluation': 'test'},
            confidence=0.8,
            reasoning='Test evaluation',
            target_metadata=target_metadata,
            snapshot_id='1'
        )
        
        coordinator.result_manager.add_result(conversation_id, result)
        
        # Get latest results through coordinator
        latest_results = coordinator.get_latest_results(conversation_id, '1')
        assert len(latest_results) == 1
        assert latest_results[0].agent_type == 'content_evaluator'
    
    def test_coordinator_get_results_by_target_type(self):
        """Test coordinator's get_results_by_target_type method"""
        conversation_id = "test_conversation_target_type"
        
        # Add results with different target types
        argument_result = coordinator.create_agent_result(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={'evaluation': 'argument'},
            confidence=0.8,
            reasoning='Argument evaluation',
            target_metadata=TargetMetadata(target_type='argument', target_content=''),
            snapshot_id='1'
        )
        
        proposition_result = coordinator.create_agent_result(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'formalization'},
            confidence=0.9,
            reasoning='Proposition formalization',
            target_metadata=TargetMetadata(target_type='proposition', target_content='Test'),
            snapshot_id='1'
        )
        
        coordinator.result_manager.add_result(conversation_id, argument_result)
        coordinator.result_manager.add_result(conversation_id, proposition_result)
        
        # Test filtering by target type
        argument_results = coordinator.get_results_by_target_type(conversation_id, 'argument', '1')
        assert len(argument_results) == 1
        assert argument_results[0].target_metadata.target_type == 'argument'
        
        proposition_results = coordinator.get_results_by_target_type(conversation_id, 'proposition', '1')
        assert len(proposition_results) == 1
        assert proposition_results[0].target_metadata.target_type == 'proposition'


if __name__ == "__main__":
    pytest.main([__file__])
