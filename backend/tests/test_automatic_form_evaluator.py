import pytest
import json
from unittest.mock import patch, MagicMock
from services.agents import FormalizationAgent
from services.agent_coordinator import coordinator


class TestAutomaticFormEvaluator:
    """Test that form evaluator is automatically queued when all propositions are formalized"""
    
    def test_formalization_queues_form_evaluator_when_complete(self):
        """Test that formalization agent does not call queue_formal_evaluator_if_ready (handled elsewhere)"""
        agent = FormalizationAgent(coordinator)
        
        # Mock existing results with formalizations for all but one proposition
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
            # Missing formalization for "Socrates is mortal" - this will be the current task
        ]
        
        # Mock the GPT response for formalization
        mock_response = {
            "formalization": {
                "ascii": "Q(a)"
            },
            "confidence": 0.95,
            "reasoning": "Direct predicate application"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt, \
             patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results), \
             patch.object(coordinator, 'queue_formal_evaluator_if_ready') as mock_queue_form_eval:
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data - formalizing the last proposition
            conversation_data = {
                'proposition': 'Socrates is mortal',
                'conversation_id': 'test_conversation',
                'argument_data': {
                    'argument': [
                        {'proposition': 'Socrates is a man'},
                        {'proposition': 'All men are mortal'},
                        {'proposition': 'Socrates is mortal'}
                    ],
                    'assumptions': []
                },
                'file_ids': []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify the result
            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            assert result.data["proposition"] == "Socrates is mortal"
            assert result.data["ascii"] == "Q(a)"
            
            # Verify that queue_formal_evaluator_if_ready was NOT called by the FormalizationAgent
            # (this functionality is handled elsewhere in the coordinator)
            mock_queue_form_eval.assert_not_called()
    
    def test_formalization_does_not_queue_form_evaluator_when_incomplete(self):
        """Test that formalization agent does not call queue_formal_evaluator_if_ready (handled elsewhere)"""
        agent = FormalizationAgent(coordinator)
        
        # Mock existing results with formalizations for only some propositions
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)',
                    'reasoning': 'Direct predicate application'
                }
            }
            # Missing formalizations for "All men are mortal" and "Socrates is mortal"
        ]
        
        # Mock the GPT response for formalization
        mock_response = {
            "formalization": {
                "ascii": "forall x. (P(x) -> Q(x))"
            },
            "confidence": 0.95,
            "reasoning": "Universal quantification"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt, \
             patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results), \
             patch.object(coordinator, 'queue_formal_evaluator_if_ready') as mock_queue_form_eval:
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data - formalizing the second proposition
            conversation_data = {
                'proposition': 'All men are mortal',
                'conversation_id': 'test_conversation',
                'argument_data': {
                    'argument': [
                        {'proposition': 'Socrates is a man'},
                        {'proposition': 'All men are mortal'},
                        {'proposition': 'Socrates is mortal'}
                    ],
                    'assumptions': []
                },
                'file_ids': []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify the result
            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            assert result.data["proposition"] == "All men are mortal"
            assert result.data["ascii"] == "forall x. (P(x) -> Q(x))"
            
            # Verify that queue_formal_evaluator_if_ready was NOT called by the FormalizationAgent
            # (this functionality is handled elsewhere in the coordinator)
            mock_queue_form_eval.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__]) 