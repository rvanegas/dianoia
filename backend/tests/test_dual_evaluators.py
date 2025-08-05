import pytest
import json
from unittest.mock import patch, MagicMock
from services.agents import ContentEvaluationAgent, FormEvaluationAgent


class TestDualEvaluators:
    """Test the dual evaluator system"""
    
    def test_content_evaluator(self):
        """Test that content evaluator works correctly"""
        agent = ContentEvaluationAgent()
        
        # Mock the GPT response for content evaluation
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
        
        with patch('services.agents.agent_gpt_evaluate_content') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            conversation_data = {
                "argument": ["Socrates is a man", "All men are mortal", "Socrates is mortal"],
                "thesis": "Socrates is mortal",
                "conversation_id": "test_conversation"
            }
            
            # Call the content evaluation agent
            result = agent.evaluate_propositions(conversation_data)
            
            # Verify the result
            assert result.agent_type == "content_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.data["evaluation_mode"] == "content"
            assert result.data["argument_validity"] == 0.95
    
    def test_form_evaluator(self):
        """Test that form evaluator works correctly"""
        agent = FormEvaluationAgent()
        
        # Mock the coordinator to return formalizations
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
        
        # Mock the GPT response for form evaluation
        mock_response = {
            "proposition_evaluations": [
                {"proposition": "Socrates is a man", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
                {"proposition": "All men are mortal", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"},
                {"proposition": "Socrates is mortal", "truth_value": 0.5, "reasoning": "Neither true nor false by form alone"}
            ],
            "argument_validity": 1.0,
            "logical_issues": [],
            "recommendations": ["Argument is deductively valid: P(a) and forall x. (P(x) -> Q(x)) logically entail Q(a)"]
        }
        
        with patch('services.agents.agent_gpt_evaluate_form') as mock_gpt, \
             patch('services.agent_coordinator.coordinator') as mock_coordinator:
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            mock_coordinator.get_conversation_results.return_value = mock_existing_results
            
            # Test data
            conversation_data = {
                "argument": ["Socrates is a man", "All men are mortal", "Socrates is mortal"],
                "thesis": "Socrates is mortal",
                "conversation_id": "test_conversation"
            }
            
            # Call the form evaluation agent
            result = agent.evaluate_propositions(conversation_data)
            
            # Verify the result
            assert result.agent_type == "form_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.data["evaluation_mode"] == "formal_validity"
            assert result.data["argument_validity"] == 1.0
            
            # Verify that all truth values are 0.5 (neither true nor false by form alone)
            for evaluation in result.data["evaluation"]["proposition_evaluations"]:
                assert evaluation["truth_value"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__]) 