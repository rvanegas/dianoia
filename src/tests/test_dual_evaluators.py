import pytest
import json
from unittest.mock import patch
from services.agents import TruthEvaluationAgent, ContentValidityEvaluationAgent, FormalEvaluatorAgent
from services.agent_coordinator import coordinator
from schemas.step import Step, Formalization
from schemas.agent_input import AgentInput, AgentData, FilteredAgentInput


class TestDualEvaluators:
    """Test that both truth and content validity evaluators work correctly, separately from form"""

    def test_truth_evaluator(self):
        """Truth evaluator returns per-step truth scores and incoherent sets"""
        agent = TruthEvaluationAgent(coordinator)

        mock_response = {
            "truth_evaluations": [
                {"symbol": "1", "truth_value": 0.95, "reasoning": "Historical fact"},
                {"symbol": "2", "truth_value": 0.98, "reasoning": "Universal biological truth"},
                {"symbol": "3", "truth_value": 0.95, "reasoning": "Well-established conclusion"}
            ],
            "incoherent_sets": []
        }

        with patch('services.agents.agent_gpt_evaluate_truth') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_data = AgentData(
                argument=[
                    Step(symbol="1", proposition="Socrates is a man", justifiers=[], truth_score=""),
                    Step(symbol="2", proposition="All men are mortal", justifiers=[], truth_score=""),
                    Step(symbol="3", proposition="Socrates is mortal", justifiers=["1", "2"], truth_score="")
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

            filtered_input = FilteredAgentInput.for_truth_evaluation(agent_input)

            # Justifiers stripped in truth filter
            for step in filtered_input.agent_data.argument:
                assert step.justifiers == []

            result = agent.evaluate_truth(filtered_input)

            assert result.agent_type == "truth_evaluator"
            assert result.operation == "evaluate_truth"
            assert len(result.result_content["truth_evaluations"]) == 3
            assert "incoherent_sets" in result.result_content

    def test_content_validity_evaluator(self):
        """Content validity evaluator returns validity scores for steps with justifiers"""
        agent = ContentValidityEvaluationAgent(coordinator)

        mock_response = {
            "validity_evaluations": [
                {"symbol": "3", "validity_value": 1.0, "reasoning": "Valid deduction from 1 and 2"}
            ],
            "logical_issues": []
        }

        with patch('services.agents.agent_gpt_evaluate_content_validity') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_data = AgentData(
                argument=[
                    Step(symbol="1", proposition="Socrates is a man", justifiers=[], truth_score=""),
                    Step(symbol="2", proposition="All men are mortal", justifiers=[], truth_score=""),
                    Step(symbol="3", proposition="Socrates is mortal", justifiers=["1", "2"], truth_score="")
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

            filtered_input = FilteredAgentInput.for_content_validity_evaluation(agent_input)

            # Justifiers preserved in content validity filter
            assert filtered_input.agent_data.argument[2].justifiers == ["1", "2"]

            result = agent.evaluate_content_validity(filtered_input)

            assert result.agent_type == "content_validity_evaluator"
            assert result.operation == "evaluate_content_validity"
            assert len(result.result_content["validity_evaluations"]) == 1
            assert result.result_content["validity_evaluations"][0]["symbol"] == "3"

    def test_form_evaluator(self):
        """Form evaluator returns validity from formal logic"""
        agent = FormalEvaluatorAgent(coordinator)

        mock_response = {
            "proposition_evaluations": [
                {"symbol": "1", "validity": 1.0, "reasoning": "Premise - no validity to evaluate"},
                {"symbol": "2", "validity": 1.0, "reasoning": "Premise - no validity to evaluate"},
                {"symbol": "3", "validity": 1.0, "reasoning": "Valid conclusion from premises 1 and 2"}
            ],
            "argument_validity": 1.0,
            "logical_issues": []
        }

        with patch('services.agents.agent_gpt_evaluate_form') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_data = AgentData(
                argument=[
                    Step(symbol="1", proposition="All men are mortal", justifiers=[], truth_score="",
                        formalization=Formalization(ascii="forall x. P(x) implies Q(x)", endorsed=True)),
                    Step(symbol="2", proposition="Socrates is a man", justifiers=[], truth_score="",
                        formalization=Formalization(ascii="P(a)", endorsed=True)),
                    Step(symbol="3", proposition="Socrates is mortal", justifiers=["1", "2"], truth_score="",
                        formalization=Formalization(ascii="Q(a)", endorsed=True))
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

            filtered_input = FilteredAgentInput.for_formal_evaluation(agent_input)
            result = agent.evaluate_propositions(filtered_input)

            assert result.agent_type == "form_evaluator"
            assert result.operation == "evaluate_propositions"
            assert result.result_content["evaluation_mode"] == "formal_validity"
            assert result.result_content["argument_validity"] == 1.0
            assert len(result.result_content["logical_issues"]) == 0


if __name__ == "__main__":
    pytest.main([__file__])
