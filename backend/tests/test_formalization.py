import pytest
import json
import re
from unittest.mock import patch, MagicMock
from services.agents import FormalizationAgent


class TestFormalizationAgent:
    """Test the formalization agent's use of abstract predicate names"""
    
    def test_formalization_uses_abstract_predicates(self):
        """Test that formalization uses abstract predicate names (P, Q, R, etc.) instead of descriptive ones"""
        agent = FormalizationAgent()
        
        # Mock the GPT response to simulate abstract predicate usage
        mock_response = {
            "formalization": {
                "ascii": "forall x. (P(x) -> Q(x))",
                "json": {
                    "type": "quantifier",
                    "quant": "forall",
                    "var": {"type": "variable", "name": "x"},
                    "body": {
                        "type": "binary",
                        "op": "implies",
                        "left": {"type": "predicate", "name": "P", "args": [{"type": "variable", "name": "x"}]},
                        "right": {"type": "predicate", "name": "Q", "args": [{"type": "variable", "name": "x"}]}
                    }
                }
            },
            "confidence": 0.9,
            "reasoning": "Universal quantification with conditional using abstract predicates P and Q"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            conversation_data = {
                "proposition": "All mice are small",
                "argument_data": {},
                "file_ids": []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify the result uses abstract predicate names
            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            assert result.data["ascii"] == "forall x. (P(x) -> Q(x))"
            assert result.data["formalization"]["ascii"] == "forall x. (P(x) -> Q(x))"
            
            # Verify that the predicate names are abstract (single letters P-Z)
            ascii_formalization = result.data["ascii"]
            import re
            predicate_pattern = r'[P-Z]\([^)]*\)'
            predicates = re.findall(predicate_pattern, ascii_formalization)
            
            # Should find abstract predicates like P(x) and Q(x)
            assert len(predicates) >= 2
            assert all(pred.startswith(('P(', 'Q(', 'R(', 'S(', 'T(', 'U(', 'V(', 'W(', 'X(', 'Y(', 'Z(')) for pred in predicates)
    
    def test_formalization_avoids_descriptive_predicates(self):
        """Test that formalization does NOT use descriptive predicate names"""
        agent = FormalizationAgent()
        
        # Mock the GPT response to simulate abstract predicate usage
        mock_response = {
            "formalization": {
                "ascii": "P(a)",
                "json": {
                    "type": "predicate",
                    "name": "P",
                    "args": [{"type": "constant", "name": "a"}]
                }
            },
            "confidence": 0.95,
            "reasoning": "Direct predicate application using abstract predicate P"
        }
        
        with patch('services.agents.agent_gpt_formalize') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            conversation_data = {
                "proposition": "Socrates is mortal",
                "argument_data": {},
                "file_ids": []
            }
            
            # Call the formalization agent
            result = agent.formalize_proposition(conversation_data)
            
            # Verify the result does NOT contain descriptive predicate names
            ascii_formalization = result.data["ascii"]
            
            # Should NOT contain descriptive predicate names
            descriptive_patterns = [
                r'is_mortal', r'is_man', r'is_mouse', r'is_small',
                r'loves', r'knows', r'believes', r'wants'
            ]
            
            for pattern in descriptive_patterns:
                assert not re.search(pattern, ascii_formalization), f"Found descriptive predicate: {pattern}"
            
            # Should contain abstract predicate names
            assert re.search(r'[P-Z]\(', ascii_formalization), "No abstract predicate found"


if __name__ == "__main__":
    pytest.main([__file__]) 