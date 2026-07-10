"""
Tests for the phrasing evaluator agent: result shape, input filtering,
and coordinator queueing alongside the other content evaluators.
"""

import json

from unittest.mock import patch

from schemas.agent_input import AgentInput, FilteredAgentInput
from schemas.arguments import ArgumentData
from schemas.step import Step
from services.agents import PhrasingEvaluationAgent
from services.agent_coordinator import coordinator


def make_agent_input(steps):
    return AgentInput(
        conversation_id="test_session:1",
        snapshot_id="1",
        agent_data={
            "argument": steps,
            "latest_results": [],
            "target_type": "argument",
            "target_content": None,
        },
        file_ids=[],
        triggered_by="user_action",
        trigger_source="argument_change",
    )


def step(symbol, proposition, justifiers=None):
    return Step(symbol=symbol, proposition=proposition,
                justifiers=justifiers or [], truth_score="")


class TestPhrasingEvaluationAgent:
    def test_evaluate_phrasing_success(self):
        agent = PhrasingEvaluationAgent(coordinator)
        agent_input = FilteredAgentInput.for_phrasing_evaluation(make_agent_input([
            step("1", "Therefore, this follows.", justifiers=["2"]),
        ]))
        response = json.dumps({"phrasing_evaluations": [{
            "symbol": "1",
            "issues": ["Begins with the inferential transition 'Therefore'"],
            "recommendation": "Drop 'Therefore' and state the claim directly.",
        }]})
        with patch("services.agents.agent_gpt_evaluate_phrasing.call",
                   return_value=response):
            result = agent.evaluate_phrasing(agent_input)
        assert result.agent_type == "phrasing_evaluator"
        assert result.operation == "evaluate_phrasing"
        evals = result.result_content["phrasing_evaluations"]
        assert evals[0]["symbol"] == "1"
        assert evals[0]["issues"]

    def test_evaluate_phrasing_error_handling(self):
        agent = PhrasingEvaluationAgent(coordinator)
        agent_input = FilteredAgentInput.for_phrasing_evaluation(
            make_agent_input([step("1", "P.")]))
        with patch("services.agents.agent_gpt_evaluate_phrasing.call",
                   side_effect=RuntimeError("boom")):
            result = agent.evaluate_phrasing(agent_input)
        assert result.agent_type == "phrasing_evaluator"
        assert "error" in result.result_content
        assert result.confidence == 0.0

    def test_filtered_input_strips_justifiers_and_formalization(self):
        agent_input = make_agent_input([step("2", "Q.", justifiers=["1"])])
        filtered = FilteredAgentInput.for_phrasing_evaluation(agent_input)
        assert filtered.agent_data.argument[0].justifiers == []
        assert filtered.agent_data.argument[0].formalization is None


class TestPhrasingEvaluatorQueueing:
    def test_queued_on_argument_change(self):
        argument_data = ArgumentData(
            argument=[step("1", "P."), step("2", "Q.", justifiers=["1"])],
        )
        with patch.object(coordinator, "queue_task") as mock_queue:
            coordinator.react_to_user_argument_change(
                "test_session:queue", "1", argument_data)
        queued = [c.kwargs.get("agent_type") or c.args[0]
                  for c in mock_queue.call_args_list]
        assert "phrasing_evaluator" in queued
        assert "truth_evaluator" in queued
        assert "content_validity_evaluator" in queued

    def test_agent_registered_with_coordinator(self):
        assert "phrasing_evaluator" in coordinator.agents
        assert isinstance(coordinator.agents["phrasing_evaluator"],
                          PhrasingEvaluationAgent)
