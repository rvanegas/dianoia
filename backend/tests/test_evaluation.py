import pytest
import json
from unittest.mock import patch, MagicMock
from services.agents import ContentEvaluationAgent


class TestEvaluationAgent:
    """Test the evaluation agent's dual-mode functionality"""
    
    def test_content_mode_evaluation(self):
        """Test that evaluation works correctly in content mode"""
        agent = ContentEvaluationAgent()
        
        # Mock the coordinator to return no formalizations (content mode)
        mock_existing_results = []
        
        # Mock the GPT response for content mode
        mock_response = {
            "proposition_evaluations": [
                {"proposition": "Socrates is a man", "truth_value": 0.9, "reasoning": "Historical fact"},
                {"proposition": "All men are mortal", "truth_value": 0.95, "reasoning": "Universal biological truth"},
                {"proposition": "Socrates is mortal", "truth_value": 0.9, "reasoning": "Valid conclusion from premises"}
            ],
            "argument_validity": 0.95,
            "logical_issues": [],
            "recommendations": ["Argument is logically sound and well-structured"]
        }
        
        with patch('services.agents.agent_gpt_evaluate_content') as mock_gpt, \
             patch('services.agent_coordinator.coordinator') as mock_coordinator:
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            mock_coordinator.get_conversation_results.return_value = mock_existing_results
            
            # Test data
            conversation_data = {
                "argument": ["Socrates is a man", "All men are mortal", "Socrates is mortal"],
                "thesis": "Socrates is mortal",
                "conversation_id": "test_conversation"
            }
            
            # Call the evaluation agent
            result = agent.evaluate_propositions(conversation_data)
            
            # Verify the result is in content mode
            assert result.agent_type == "content_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.data["evaluation_mode"] == "content"
            assert result.data["argument_validity"] == 0.95
            
            # Verify that the evaluator was called with content mode
            call_args = mock_gpt.call.call_args[0][0]
            call_data = json.loads(call_args)
            # The content evaluator doesn't need evaluation_mode in the call data
            assert 'argument' in call_data
    
    def test_content_evaluator_always_evaluates_content(self):
        """Test that content evaluator always evaluates content, regardless of formalizations"""
        agent = ContentEvaluationAgent()
        
        # Mock the coordinator to return formalizations (but content evaluator ignores them)
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)',
                    'reasoning': 'Direct predicate application'
                }
            }
        ]
        
        # Mock the GPT response for content evaluation
        mock_response = {
            "proposition_evaluations": [
                {"proposition": "Socrates is a man", "truth_value": 0.9, "reasoning": "Historical fact"}
            ],
            "argument_validity": 0.9,
            "logical_issues": [],
            "recommendations": ["Argument is sound"]
        }
        
        with patch('services.agents.agent_gpt_evaluate_content') as mock_gpt, \
             patch('services.agent_coordinator.coordinator') as mock_coordinator:
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            mock_coordinator.get_conversation_results.return_value = mock_existing_results
            
            # Test data
            conversation_data = {
                "argument": ["Socrates is a man"],
                "thesis": "Socrates is mortal",
                "conversation_id": "test_conversation"
            }
            
            # Call the evaluation agent
            result = agent.evaluate_propositions(conversation_data)
            
            # Verify the result is always in content mode
            assert result.agent_type == "content_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.data["evaluation_mode"] == "content"
            assert result.data["argument_validity"] == 0.9
            
            # Verify that the evaluator was called with content evaluation
            call_args = mock_gpt.call.call_args[0][0]
            call_data = json.loads(call_args)
            assert 'argument' in call_data
    
    def test_content_evaluator_ignores_formalizations(self):
        """Test that content evaluator ignores formalizations and always evaluates content"""
        agent = ContentEvaluationAgent()
        
        # Test with formalizations present (content evaluator should ignore them)
        mock_with_formalizations = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'Socrates is a man',
                    'ascii': 'P(a)',
                    'reasoning': 'Direct predicate application'
                }
            }
        ]
        
        with patch('services.agent_coordinator.coordinator') as mock_coordinator:
            mock_coordinator.get_conversation_results.return_value = mock_with_formalizations
            
            conversation_data = {
                "argument": ["Socrates is a man"],
                "conversation_id": "test_conversation"
            }
            
            # The content evaluator should always evaluate content, regardless of formalizations
            result = agent.evaluate_propositions(conversation_data)
            assert result.agent_type == "content_evaluator"
            assert result.data["evaluation_mode"] == "content"


if __name__ == "__main__":
    pytest.main([__file__]) 