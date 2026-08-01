import pytest
import json
from unittest.mock import patch
from services.agents import TruthEvaluationAgent, ContentValidityEvaluationAgent
from services.agent_coordinator import coordinator
from schemas.agent_input import FilteredAgentInput, AgentData
from schemas.step import Step


class TestTruthEvaluationAgent:
    """Test the truth evaluation agent"""

    def test_evaluates_truth_independently(self):
        """Truth evaluation assigns scores to all argument steps"""
        agent = TruthEvaluationAgent(coordinator)

        mock_response = {
            "truth_evaluations": [
                {"symbol": "1", "truth_value": 0.95, "reasoning": "Historical fact"},
                {"symbol": "2", "truth_value": 0.98, "reasoning": "Universal biological truth"},
                {"symbol": "3", "truth_value": 0.95, "reasoning": "Well-established fact"}
            ],
            "incoherent_sets": []
        }

        with patch('services.agents.agent_gpt_evaluate_truth') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_input = FilteredAgentInput(
                conversation_id='test_conversation',
                snapshot_id='test_snapshot',
                agent_data=AgentData(
                    argument=[
                        Step(symbol='1', proposition='Socrates is a man', justifiers=[], truth_score=''),
                        Step(symbol='2', proposition='All men are mortal', justifiers=[], truth_score=''),
                        Step(symbol='3', proposition='Socrates is mortal', justifiers=['1', '2'], truth_score=''),
                    ],
                    latest_results=[],
                    target_type='argument',
                    target_content=None
                ),
                file_ids=[]
            )

            filtered = FilteredAgentInput.for_truth_evaluation(agent_input)

            # Justifiers must be stripped before sending
            for step in filtered.agent_data.argument:
                assert step.justifiers == []

            result = agent.evaluate_truth(filtered)

            assert result.agent_type == 'truth_evaluator'
            assert result.operation == 'evaluate_truth'
            assert len(result.result_content['truth_evaluations']) == 3

    def test_evaluates_every_step_including_former_assumptions(self):
        """Truth evaluator evaluates every step in the single argument list"""
        agent = TruthEvaluationAgent(coordinator)

        mock_response = {
            "truth_evaluations": [
                {"symbol": "1", "truth_value": 0.0, "reasoning": "False — the sun has no legs"},
                {"symbol": "2", "truth_value": 0.0, "reasoning": "False — the sun has no legs"}
            ],
            "incoherent_sets": []
        }

        with patch('services.agents.agent_gpt_evaluate_truth') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_input = FilteredAgentInput(
                conversation_id='test_conversation',
                snapshot_id='test_snapshot',
                agent_data=AgentData(
                    argument=[
                        Step(symbol='1', proposition='The sun has four legs', justifiers=[], truth_score=''),
                        Step(symbol='2', proposition='The sun has legs', justifiers=[], truth_score='')
                    ],
                    latest_results=[],
                    target_type='argument',
                    target_content=None
                ),
                file_ids=[]
            )

            result = agent.evaluate_truth(FilteredAgentInput.for_truth_evaluation(agent_input))
            assert result.agent_type == 'truth_evaluator'
            assert len(result.result_content['truth_evaluations']) == 2
            symbols = {e['symbol'] for e in result.result_content['truth_evaluations']}
            assert symbols == {'1', '2'}


class TestContentValidityEvaluationAgent:
    """Test the content validity evaluation agent"""

    def test_evaluates_only_steps_with_justifiers(self):
        """Content validity is only assigned to steps that have justifiers"""
        agent = ContentValidityEvaluationAgent(coordinator)

        mock_response = {
            "validity_evaluations": [
                {"symbol": "3", "validity_value": 1.0, "reasoning": "Valid deduction from 1 and 2"}
            ],
            "logical_issues": []
        }

        with patch('services.agents.agent_gpt_evaluate_content_validity') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_input = FilteredAgentInput(
                conversation_id='test_conversation',
                snapshot_id='test_snapshot',
                agent_data=AgentData(
                    argument=[
                        Step(symbol='1', proposition='Socrates is a man', justifiers=[], truth_score=''),
                        Step(symbol='2', proposition='All men are mortal', justifiers=[], truth_score=''),
                        Step(symbol='3', proposition='Socrates is mortal', justifiers=['1', '2'], truth_score=''),
                    ],
                    latest_results=[],
                    target_type='argument',
                    target_content=None
                ),
                file_ids=[]
            )

            result = agent.evaluate_content_validity(
                FilteredAgentInput.for_content_validity_evaluation(agent_input)
            )

            assert result.agent_type == 'content_validity_evaluator'
            assert result.operation == 'evaluate_content_validity'
            assert len(result.result_content['validity_evaluations']) == 1
            assert result.result_content['validity_evaluations'][0]['symbol'] == '3'

    def test_justifiers_preserved(self):
        """Content validity filter preserves justifiers"""
        agent_input = FilteredAgentInput(
            conversation_id='test_conversation',
            snapshot_id='test_snapshot',
            agent_data=AgentData(
                argument=[
                    Step(symbol='1', proposition='P1', justifiers=[], truth_score=''),
                    Step(symbol='2', proposition='P2', justifiers=['1'], truth_score=''),
                ],
                latest_results=[],
                target_type='argument',
                target_content=None
            ),
            file_ids=[]
        )

        filtered = FilteredAgentInput.for_content_validity_evaluation(agent_input)
        assert filtered.agent_data.argument[1].justifiers == ['1']


if __name__ == "__main__":
    pytest.main([__file__])
