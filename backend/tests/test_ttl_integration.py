import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app

client = TestClient(app)


class TestTTLIntegration:
    """Test TTL cleanup integration with API endpoints"""
    
    def test_argue_endpoint_triggers_cleanup(self):
        """Test that the argue endpoint calls cleanup_expired_conversations"""
        with patch('services.agent_coordinator.coordinator.result_manager.cleanup_expired_conversations') as mock_cleanup:
            mock_cleanup.return_value = 2  # Simulate cleaning up 2 conversations
            
            response = client.post(
                "/api/argument/argue",
                params={
                    "session_id": "test_session_123",
                    "conversation_id": "1"
                },
                json={
                    "proposition": "Socrates is mortal",
                    "assumptions": [],
                    "argument": [],
                    "file_ids": []
                }
            )
            
            assert response.status_code == 200
            # Verify cleanup was called
            mock_cleanup.assert_called_once()
            
            # Verify the response still works normally
            result = response.json()
            assert "reply" in result
