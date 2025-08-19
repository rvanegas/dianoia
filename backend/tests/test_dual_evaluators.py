import pytest
import json
from unittest.mock import patch
from services.agents import ContentEvaluationAgent, FormEvaluationAgent
from services.agent_coordinator import coordinator
from schemas.step import Step
from schemas.agent_input import AgentInput, AgentData, FilteredAgentInput


class TestDualEvaluators:
    """Test that both content and form evaluators work correctly"""
    
    def test_content_evaluator(self):
        """Test that content evaluator works correctly"""
        agent = ContentEvaluationAgent(coordinator)
        
        # Mock the GPT response for content evaluation
        mock_response = {
            "proposition_evaluations": [
                {"proposition": "Socrates is a man", "truth_value": 0.9, "reasoning": "Historical fact"},
                {"proposition": "All men are mortal", "truth_value": 0.95, "reasoning": "Universal biological truth"},
                {"proposition": "Socrates is mortal", "truth_value": 0.9, "reasoning": "Valid conclusion from premises"}
            ],
            "overall_truth_score": 0.95,
            "truth_issues": [],
            "recommendations": ["Argument is logically sound and well-structured"]
        }
        
        with patch('services.agents.agent_gpt_evaluate_content') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            agent_data = AgentData(
                assumptions=[],
                argument=[
                    Step(symbol="A", proposition="Socrates is a man", justifiers=[], truth="1.0", valid="1.0"),
                    Step(symbol="B", proposition="All men are mortal", justifiers=[], truth="1.0", valid="1.0"),
                    Step(symbol="C", proposition="Socrates is mortal", justifiers=["A", "B"], truth="1.0", valid="1.0")
                ],
                latest_results=[],
                target_type="argument",
                target_content=None
            )
            agent_input = AgentInput(
                conversation_id="test_conversation",
                snapshot_id="test_snapshot_123",
                
                file_ids=[],
                agent_data=agent_data
            )
            
            # Create FilteredAgentInput for content evaluation
            filtered_input = FilteredAgentInput.for_content_evaluation(agent_input)
            # Call the content evaluation agent
            result = agent.evaluate_propositions(filtered_input)
            
            # Verify the result
            assert result.agent_type == "content_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.result_content["evaluation_mode"] == "content_truth"
    
    def test_form_evaluator(self):
        """Test that form evaluator works correctly"""
        agent = FormEvaluationAgent(coordinator)
        

        
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
        
        with patch('services.agents.agent_gpt_evaluate_form') as mock_gpt:
            
            mock_gpt.call.return_value = json.dumps(mock_response)
            
            # Test data
            agent_data = AgentData(
                assumptions=[],
                argument=[
                    Step(symbol="A", proposition="All men are mortal", justifiers=[], truth="1.0", valid="1.0", formalization="forall x. (P(x) -> Q(x))"),
                    Step(symbol="B", proposition="Socrates is a man", justifiers=[], truth="1.0", valid="1.0", formalization="P(a)"),
                    Step(symbol="C", proposition="Socrates is mortal", justifiers=["A", "B"], truth="1.0", valid="1.0", formalization="Q(a)")
                ],
                latest_results=[],
                target_type="argument",
                target_content=None
            )
            agent_input = AgentInput(
                conversation_id="test_session:1",
                snapshot_id="test_snapshot_123",
                file_ids=[],
                agent_data=agent_data
            )
            
            # Create FilteredAgentInput for form evaluation
            filtered_input = FilteredAgentInput.for_formal_evaluation(agent_input)
            # Call the form evaluation agent
            result = agent.evaluate_propositions(filtered_input)
            
            # Verify the result
            assert result.agent_type == "form_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.result_content["evaluation_mode"] == "formal_validity"
            assert result.result_content["argument_validity"] == 1.0
            assert result.result_content["proposition_count"] == 3
            assert len(result.result_content["logical_issues"]) == 0
            assert len(result.result_content["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__]) 