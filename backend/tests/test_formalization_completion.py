import pytest
from unittest.mock import patch, MagicMock
from services.agent_coordinator import coordinator


class TestFormalizationCompletion:
    """Test the formalization completion check functionality"""
    
    def test_check_formalization_completion_all_formalized(self):
        """Test that completion check returns True when all propositions are formalized"""
        # Mock existing results with formalizations for all propositions
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)',
                    'reasoning': 'Direct predicate application'
                }
            },
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'All men are mortal',
                    'ascii': 'forall x. (P(x) -> Q(x))',
                    'reasoning': 'Universal quantification'
                }
            },
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is mortal',
                    'ascii': 'Q(a)',
                    'reasoning': 'Direct predicate application'
                }
            }
        ]
        
        with patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results):
            # Test with all propositions formalized
            argument = ["Socrates is a man", "All men are mortal", "Socrates is mortal"]
            conversation_id = "test_conversation"
            
            result = coordinator.check_formalization_completion(conversation_id, argument)
            
            assert result == True
    
    def test_check_formalization_completion_partial_formalized(self):
        """Test that completion check returns False when only some propositions are formalized"""
        # Mock existing results with formalizations for only some propositions
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)',
                    'reasoning': 'Direct predicate application'
                }
            },
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'All men are mortal',
                    'ascii': 'forall x. (P(x) -> Q(x))',
                    'reasoning': 'Universal quantification'
                }
            }
            # Missing formalization for "Socrates is mortal"
        ]
        
        with patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results):
            # Test with only some propositions formalized
            argument = ["Socrates is a man", "All men are mortal", "Socrates is mortal"]
            conversation_id = "test_conversation"
            
            result = coordinator.check_formalization_completion(conversation_id, argument)
            
            assert result == False
    
    def test_check_formalization_completion_no_formalizations(self):
        """Test that completion check returns False when no formalizations exist"""
        # Mock existing results with no formalizations
        mock_existing_results = []
        
        with patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results):
            # Test with no formalizations
            argument = ["Socrates is a man", "All men are mortal", "Socrates is mortal"]
            conversation_id = "test_conversation"
            
            result = coordinator.check_formalization_completion(conversation_id, argument)
            
            assert result == False
    
    def test_check_formalization_completion_empty_argument(self):
        """Test that completion check returns True for empty argument"""
        # Mock existing results
        mock_existing_results = []
        
        with patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results):
            # Test with empty argument
            argument = []
            conversation_id = "test_conversation"
            
            result = coordinator.check_formalization_completion(conversation_id, argument)
            
            assert result == True  # Empty argument is considered complete
    
    def test_check_formalization_completion_error_handling(self):
        """Test that completion check handles errors gracefully"""
        with patch.object(coordinator, 'get_conversation_results', side_effect=Exception("Test error")):
            # Test error handling
            argument = ["Socrates is a man"]
            conversation_id = "test_conversation"
            
            result = coordinator.check_formalization_completion(conversation_id, argument)
            
            assert result == False  # Should return False on error


if __name__ == "__main__":
    pytest.main([__file__]) 