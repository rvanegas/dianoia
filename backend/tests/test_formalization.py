import pytest
import json
from unittest.mock import patch
from services.agents import FormalizationAgent
from services.agent_coordinator import coordinator


class TestFormalizationAgent:
    """Test the formalization agent functionality"""
    
    def test_formalization_uses_abstract_predicates(self):
        """Test that formalization uses abstract predicate names (P, Q, R, etc.) instead of descriptive ones"""
        agent = FormalizationAgent(coordinator)
        
        # Mock the GPT response to simulate abstract predicate usage
        mock_response = {
            "formalization": {
                "ascii": "forall x. (P(x) -> Q(x))"
            },
            "confidence": 0.9,
            "reasoning": "Universal quantification with conditional using abstract predicates P and Q"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            conversation_data = {
                "proposition": "All mice are small",
                "conversation_id": "test_conversation",
                "argument_data": {},
                "file_ids": []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify the result uses abstract predicate names
            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            assert result.data["ascii"] == "forall x. (P(x) -> Q(x))"
    
    def test_formalization_avoids_descriptive_predicates(self):
        """Test that formalization does NOT use descriptive predicate names"""
        agent = FormalizationAgent(coordinator)
        
        # Mock the GPT response to simulate abstract predicate usage
        mock_response = {
            "formalization": {
                "ascii": "P(a)"
            },
            "confidence": 0.95,
            "reasoning": "Direct predicate application using abstract predicate P"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            conversation_data = {
                "proposition": "Socrates is mortal",
                "conversation_id": "test_conversation",
                "argument_data": {},
                "file_ids": []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify the result does NOT contain descriptive predicate names
            ascii_formalization = result.data["ascii"]
            assert "Socrates" not in ascii_formalization
            assert "mortal" not in ascii_formalization
            assert "is" not in ascii_formalization
            assert "P(a)" in ascii_formalization
    
    def test_formalization_maintains_consistency(self):
        """Test that formalization maintains consistency with existing formalizations"""
        agent = FormalizationAgent(coordinator)
        
        # Mock the coordinator to return existing formalizations
        mock_existing_results = [
            {
                'agent_type': 'formalizer',
                'data': {
                    'proposition': 'All mice are small',
                    'ascii': 'forall x. (P(x) -> Q(x))',
                    'reasoning': 'Universal quantification using P for mouse and Q for small'
                }
            }
        ]
        
        # Mock the GPT response to simulate consistent formalization
        mock_response = {
            "formalization": {
                "ascii": "P(a)"
            },
            "confidence": 0.95,
            "reasoning": "Consistent with existing formalization: using P for mouse as established"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt, \
             patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results):
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            conversation_data = {
                "proposition": "This mouse is small",
                "conversation_id": "test_conversation",
                "argument_data": {},
                "file_ids": []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify that the formalizer was called with existing formalizations
            call_args = mock_gpt.call.call_args[0][0]
            call_data = json.loads(call_args)
            
            # Should include existing formalizations in the call
            assert 'existing_formalizations' in call_data
            assert len(call_data['existing_formalizations']) == 1
            
            # Verify the result
            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            assert result.data["ascii"] == "P(a)"


if __name__ == "__main__":
    pytest.main([__file__]) 