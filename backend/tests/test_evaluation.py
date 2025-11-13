import pytest
import json
from unittest.mock import patch, MagicMock
from services.agents import EvaluationAgent


class TestEvaluationAgent:
    """Test the evaluation agent's dual-mode functionality"""
    
    def test_content_mode_evaluation(self):
        """Test that evaluation works correctly in content mode"""
        agent = EvaluationAgent()
        
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
        
        with patch('services.agents.agent_gpt_evaluate') as mock_gpt, \
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
            assert result.agent_type == "evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.data["evaluation_mode"] == "content"
            assert result.data["argument_validity"] == 0.95
            
            # Verify that the evaluator was called with content mode
            call_args = mock_gpt.call.call_args[0][0]
            call_data = json.loads(call_args)
            assert call_data['evaluation_mode'] == "content"
    
    def test_formal_validity_mode_evaluation(self):
        """Test that evaluation works correctly in formal validity mode"""
        agent = EvaluationAgent()
        
        # Mock the coordinator to return formalizations (formal validity mode)
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
        
        # Mock the GPT response for formal validity mode
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
        
        with patch('services.agents.agent_gpt_evaluate') as mock_gpt, \
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
            
            # Verify the result is in formal validity mode
            assert result.agent_type == "evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.data["evaluation_mode"] == "formal_validity"
            assert result.data["argument_validity"] == 1.0
            
            # Verify that all proposition truth values are 0.5 (neither true nor false by form alone)
            for evaluation in result.data["evaluation"]["proposition_evaluations"]:
                assert evaluation["truth_value"] == 0.5
            
            # Verify that the evaluator was called with formal validity mode and formalizations
            call_args = mock_gpt.call.call_args[0][0]
            call_data = json.loads(call_args)
            assert call_data['evaluation_mode'] == "formal_validity"
            assert 'formalizations' in call_data
            assert call_data['formalizations'] == ['P(a)', 'forall x. (P(x) -> Q(x))', 'Q(a)']
    
    def test_evaluation_mode_detection(self):
        """Test that evaluation mode is correctly detected based on formalizations"""
        agent = EvaluationAgent()
        
        # Test with no formalizations (should be content mode)
        mock_no_formalizations = []
        
        with patch('services.agent_coordinator.coordinator') as mock_coordinator:
            mock_coordinator.get_conversation_results.return_value = mock_no_formalizations
            
            conversation_data = {
                "argument": ["Socrates is a man", "All men are mortal", "Socrates is mortal"],
                "conversation_id": "test_conversation"
            }
            
            mode = agent._determine_evaluation_mode(conversation_data)
            assert mode == "content"
        
        # Test with formalizations for all propositions (should be formal validity mode)
        mock_with_formalizations = [
            {'agent_type': 'formalizer', 'data': {'proposition': 'Socrates is a man'}},
            {'agent_type': 'formalizer', 'data': {'proposition': 'All men are mortal'}},
            {'agent_type': 'formalizer', 'data': {'proposition': 'Socrates is mortal'}}
        ]
        
        with patch('services.agent_coordinator.coordinator') as mock_coordinator:
            mock_coordinator.get_conversation_results.return_value = mock_with_formalizations
            
            conversation_data = {
                "argument": ["Socrates is a man", "All men are mortal", "Socrates is mortal"],
                "conversation_id": "test_conversation"
            }
            
            mode = agent._determine_evaluation_mode(conversation_data)
            assert mode == "formal_validity"


if __name__ == "__main__":
    pytest.main([__file__]) 