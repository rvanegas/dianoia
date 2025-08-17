import pytest
import time
from services.agent_coordinator import AgentResultManager


class TestTTLFunctionality:
    """Test TTL functionality in AgentResultManager"""
    
    def test_ttl_removes_old_conversation(self):
        """Test that conversations older than 3 days are removed by cleanup"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add a test result
        test_result = {
            'agent_type': 'builder',
            'operation': 'build_argument',
            'data': {'proposition': 'Test proposition'}
        }
        result_manager.add_result(conversation_id, test_result)
        
        # Verify result is added
        results = result_manager.get_results(conversation_id)
        assert len(results) == 1
        assert results[0]['data']['proposition'] == 'Test proposition'
        
        # Manually set the conversation timestamp to be old (4 days ago)
        old_timestamp = time.time() - (4 * 24 * 60 * 60)  # 4 days ago
        result_manager.conversation_timestamps[conversation_id] = old_timestamp
        
        # Get results - should still return results (no cleanup during retrieval)
        results = result_manager.get_results(conversation_id)
        assert len(results) == 1
        
        # Manually set timestamp to old again (get_results updated it)
        result_manager.conversation_timestamps[conversation_id] = old_timestamp
        
        # Run cleanup - should remove the expired conversation
        removed_count = result_manager.cleanup_expired_conversations()
        assert removed_count == 1
        
        # Verify conversation is completely removed
        assert conversation_id not in result_manager.results_by_conversation
        assert conversation_id not in result_manager.conversation_timestamps
    
    def test_ttl_keeps_recent_conversation(self):
        """Test that recent conversations are kept"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add a test result
        test_result = {
            'agent_type': 'formalizer',
            'operation': 'formalize_proposition',
            'data': {'proposition': 'Recent proposition'}
        }
        result_manager.add_result(conversation_id, test_result)
        
        # Verify result is kept (should be recent)
        results = result_manager.get_results(conversation_id)
        assert len(results) == 1
        assert results[0]['data']['proposition'] == 'Recent proposition'
    
    def test_ttl_updates_timestamp_on_activity(self):
        """Test that conversation timestamp is updated on activity"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add a test result
        test_result = {
            'agent_type': 'content_evaluator',
            'operation': 'evaluate_propositions',
            'data': {'proposition': 'Test proposition'}
        }
        result_manager.add_result(conversation_id, test_result)
        
        # Get initial timestamp
        initial_timestamp = result_manager.conversation_timestamps[conversation_id]
        
        # Wait a moment and get results again
        time.sleep(0.1)
        result_manager.get_results(conversation_id)
        
        # Verify timestamp was updated
        updated_timestamp = result_manager.conversation_timestamps[conversation_id]
        assert updated_timestamp > initial_timestamp
    
    def test_cleanup_expired_conversations(self):
        """Test the cleanup method specifically"""
        result_manager = AgentResultManager()
        
        # Add multiple conversations
        for i in range(3):
            conversation_id = f"test_conversation_{i}"
            test_result = {
                'agent_type': 'builder',
                'operation': 'build_argument',
                'data': {'proposition': f'Test proposition {i}'}
            }
            result_manager.add_result(conversation_id, test_result)
        
        # Make two conversations old
        old_timestamp = time.time() - (4 * 24 * 60 * 60)  # 4 days ago
        result_manager.conversation_timestamps["test_conversation_0"] = old_timestamp
        result_manager.conversation_timestamps["test_conversation_1"] = old_timestamp
        
        # Run cleanup
        removed_count = result_manager.cleanup_expired_conversations()
        assert removed_count == 2
        
        # Verify old conversations are removed
        assert "test_conversation_0" not in result_manager.results_by_conversation
        assert "test_conversation_1" not in result_manager.results_by_conversation
        assert "test_conversation_2" in result_manager.results_by_conversation  # Still active
    
    def test_ttl_cleanup_on_conversation_cleanup(self):
        """Test that conversation cleanup removes timestamps"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add a test result
        test_result = {
            'agent_type': 'content_evaluator',
            'operation': 'evaluate_propositions',
            'data': {'proposition': 'Test proposition'}
        }
        result_manager.add_result(conversation_id, test_result)
        
        # Verify both results and timestamps exist
        assert conversation_id in result_manager.results_by_conversation
        assert conversation_id in result_manager.conversation_timestamps
        
        # Clean up conversation
        result_manager.cleanup_conversation(conversation_id)
        
        # Verify both are removed
        assert conversation_id not in result_manager.results_by_conversation
        assert conversation_id not in result_manager.conversation_timestamps
