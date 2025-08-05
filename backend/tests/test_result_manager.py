import pytest
from unittest.mock import patch, MagicMock
from services.agent_coordinator import coordinator, AgentResultManager


class TestResultManager:
    """Test the result manager's handling of form evaluator results"""
    
    def test_result_manager_maintains_one_form_evaluator_when_complete(self):
        """Test that result manager maintains only one form evaluator result when all propositions are formalized"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Mock existing formalization results
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)'
                }
            },
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'All men are mortal',
                    'ascii': 'forall x. (P(x) -> Q(x))'
                }
            },
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is mortal',
                    'ascii': 'Q(a)'
                }
            }
        ]
        
        # Mock the coordinator to return these results and indicate completion
        with patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results), \
             patch.object(coordinator, 'check_formalization_completion', return_value=True):
            
            # Add a form evaluator result
            form_evaluator_result = {
                'agent_type': 'form_evaluator',
                'data': {
                    'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                    'evaluation': {
                        'proposition_evaluations': [
                            {'proposition': 'Socrates is a man', 'truth_value': 0.5},
                            {'proposition': 'All men are mortal', 'truth_value': 0.5},
                            {'proposition': 'Socrates is mortal', 'truth_value': 0.5}
                        ],
                        'argument_validity': 1.0
                    }
                }
            }
            
            result_manager.add_result(conversation_id, form_evaluator_result)
            
            # Verify the result was added
            results = result_manager.get_results(conversation_id)
            form_evaluator_results = [r for r in results if r.get('agent_type') == 'form_evaluator']
            assert len(form_evaluator_results) == 1
            
            # Add another form evaluator result (should replace the first)
            new_form_evaluator_result = {
                'agent_type': 'form_evaluator',
                'data': {
                    'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                    'evaluation': {
                        'proposition_evaluations': [
                            {'proposition': 'Socrates is a man', 'truth_value': 0.5},
                            {'proposition': 'All men are mortal', 'truth_value': 0.5},
                            {'proposition': 'Socrates is mortal', 'truth_value': 0.5}
                        ],
                        'argument_validity': 0.8  # Different validity
                    }
                }
            }
            
            result_manager.add_result(conversation_id, new_form_evaluator_result)
            
            # Verify only one form evaluator result remains
            results = result_manager.get_results(conversation_id)
            form_evaluator_results = [r for r in results if r.get('agent_type') == 'form_evaluator']
            assert len(form_evaluator_results) == 1
            assert form_evaluator_results[0]['data']['evaluation']['argument_validity'] == 0.8
    
    def test_result_manager_removes_form_evaluator_when_incomplete(self):
        """Test that result manager removes form evaluator results when not all propositions are formalized"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Mock existing formalization results (incomplete)
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)'
                }
            }
            # Missing formalizations for "All men are mortal" and "Socrates is mortal"
        ]
        
        # Mock the coordinator to return these results and indicate incompletion
        with patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results), \
             patch.object(coordinator, 'check_formalization_completion', return_value=False):
            
            # Add a form evaluator result (this shouldn't exist but let's test cleanup)
            form_evaluator_result = {
                'agent_type': 'form_evaluator',
                'data': {
                    'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                    'evaluation': {
                        'proposition_evaluations': [
                            {'proposition': 'Socrates is a man', 'truth_value': 0.5},
                            {'proposition': 'All men are mortal', 'truth_value': 0.5},
                            {'proposition': 'Socrates is mortal', 'truth_value': 0.5}
                        ],
                        'argument_validity': 1.0
                    }
                }
            }
            
            # Add the result - it should be removed during the add process due to incomplete formalization
            result_manager.add_result(conversation_id, form_evaluator_result)
            
            # Verify the result was removed due to incomplete formalization
            results = result_manager.get_results(conversation_id)
            form_evaluator_results = [r for r in results if r.get('agent_type') == 'form_evaluator']
            assert len(form_evaluator_results) == 0
    
    def test_result_manager_maintains_content_evaluator_independently(self):
        """Test that result manager maintains content evaluator results independently"""
        result_manager = AgentResultManager()
        conversation_id = "test_conversation"
        
        # Add a content evaluator result
        content_evaluator_result = {
            'agent_type': 'content_evaluator',
            'data': {
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.9},
                        {'proposition': 'All men are mortal', 'truth_value': 0.95},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.9}
                    ],
                    'argument_validity': 0.95
                }
            }
        }
        
        result_manager.add_result(conversation_id, content_evaluator_result)
        
        # Verify the content evaluator result was added
        results = result_manager.get_results(conversation_id)
        content_evaluator_results = [r for r in results if r.get('agent_type') == 'content_evaluator']
        assert len(content_evaluator_results) == 1
        
        # Add another content evaluator result (should replace the first)
        new_content_evaluator_result = {
            'agent_type': 'content_evaluator',
            'data': {
                'argument': ['Socrates is a man', 'All men are mortal', 'Socrates is mortal'],
                'evaluation': {
                    'proposition_evaluations': [
                        {'proposition': 'Socrates is a man', 'truth_value': 0.8},
                        {'proposition': 'All men are mortal', 'truth_value': 0.85},
                        {'proposition': 'Socrates is mortal', 'truth_value': 0.8}
                    ],
                    'argument_validity': 0.85
                }
            }
        }
        
        result_manager.add_result(conversation_id, new_content_evaluator_result)
        
        # Verify only one content evaluator result remains
        results = result_manager.get_results(conversation_id)
        content_evaluator_results = [r for r in results if r.get('agent_type') == 'content_evaluator']
        assert len(content_evaluator_results) == 1
        assert content_evaluator_results[0]['data']['evaluation']['argument_validity'] == 0.85


if __name__ == "__main__":
    pytest.main([__file__]) 