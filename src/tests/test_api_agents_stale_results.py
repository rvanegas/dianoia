import pytest
from fastapi.testclient import TestClient
from main import app
from services.agent_coordinator import coordinator, TargetMetadata
import time

client = TestClient(app)


class TestAgentsAPIWithStaleResults:
    """Test the updated agents API endpoints using StaleResultsPropagation"""
    
    def setup_method(self):
        """Set up test data"""
        self.conversation_id = "test_session:123"
        self.snapshot_id = "2"
        
        # Add some test results with different snapshots
        # Use different agent types to avoid the "latest per agent type" logic
        result_1 = coordinator.create_agent_result(
            agent_type='formalizer',
            operation='formalize_proposition',
            result_content={'proposition': 'Socrates is a man', 'ascii': 'P(a)'},
            confidence=0.9,
            reasoning='Snapshot 1 formalization',
            target_metadata=TargetMetadata(target_type='proposition', target_content='Socrates is a man'),
            snapshot_id='1'
        )
        coordinator.result_manager.add_result(self.conversation_id, result_1)
        
        result_2 = coordinator.create_agent_result(
            agent_type='content_evaluator',
            operation='evaluate_propositions',
            result_content={'evaluation': {'argument_validity': 0.95}},
            confidence=0.95,
            reasoning='Snapshot 2 evaluation',
            target_metadata=TargetMetadata(target_type='argument', target_content=''),
            snapshot_id='2'
        )
        coordinator.result_manager.add_result(self.conversation_id, result_2)
    
    def test_get_results_with_snapshot_filtering(self):
        """Test that the /results endpoint filters by snapshot correctly"""
        response = client.get(
            "/api/agents/results",
            params={
                "conversation_id": self.conversation_id,
                "snapshot_id": self.snapshot_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "conversation_id" in data
        assert "snapshot_id" in data
        assert "results_by_agent" in data
        assert "total_count" in data
        assert "agent_types" in data
        assert "tasks_complete" in data
        
        # Verify snapshot filtering - should get results from snapshots <= 2
        assert data["snapshot_id"] == self.snapshot_id
        assert data["total_count"] == 2  # Should get 2 results (formalizer from snapshot 1, content_evaluator from snapshot 2)
        
        # Should have both agent types
        assert "formalizer" in data["results_by_agent"]
        assert "content_evaluator" in data["results_by_agent"]
        
        # Verify the formalizer result is from snapshot 1
        formalizer_result = data["results_by_agent"]["formalizer"][0]
        assert formalizer_result["snapshot_id"] == "1"
        assert formalizer_result["result_content"]["ascii"] == "P(a)"
    

    
    def test_missing_snapshot_id(self):
        """Test that missing snapshot_id returns 422"""
        response = client.get(
            "/api/agents/results",
            params={
                "conversation_id": self.conversation_id
                # Missing snapshot_id
            }
        )
        
        assert response.status_code == 422
    
    def test_missing_conversation_id(self):
        """Test that missing conversation_id returns 422"""
        response = client.get(
            "/api/agents/results",
            params={
                "snapshot_id": self.snapshot_id
                # Missing conversation_id
            }
        )
        
        assert response.status_code == 422
    
    def test_snapshot_beyond_available_results(self):
        """Test requesting a snapshot beyond available results"""
        response = client.get(
            "/api/agents/results",
            params={
                "conversation_id": self.conversation_id,
                "snapshot_id": "10"  # Future snapshot
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should get latest results per agent type (2 total: formalizer + content_evaluator)
        assert data["total_count"] == 2
        assert "formalizer" in data["results_by_agent"]
        assert "content_evaluator" in data["results_by_agent"]
        
        # Should get the formalizer result from snapshot 1 (only one we have)
        formalizer_result = data["results_by_agent"]["formalizer"][0]
        assert formalizer_result["snapshot_id"] == "1"
        assert formalizer_result["result_content"]["ascii"] == "P(a)"


if __name__ == "__main__":
    pytest.main([__file__])
