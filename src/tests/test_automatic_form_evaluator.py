import pytest
import json
from unittest.mock import patch
from services.agents import FormalizationAgent
from services.agent_coordinator import coordinator


def _mock_formalizations_response(steps):
    """Build a mock LLM formalization response in the new semantic-name format."""
    fmls = []
    for sym, semantic_pred, semantic_const in steps:
        if semantic_const:
            js = json.dumps({
                "type": "predicate",
                "name": semantic_pred,
                "args": [{"type": "constant", "name": semantic_const}]
            })
            ascii_str = f"{semantic_pred}({semantic_const})"
        else:
            js = json.dumps({
                "type": "quantifier", "quant": "forall",
                "vars": [{"type": "variable", "name": "individual"}],
                "body": {
                    "type": "connective", "op": "implies",
                    "args": [
                        {"type": "predicate", "name": semantic_pred, "args": [{"type": "variable", "name": "individual"}]},
                        {"type": "predicate", "name": "is_mortal", "args": [{"type": "variable", "name": "individual"}]}
                    ]
                }
            })
            ascii_str = f"forall individual. ({semantic_pred}(individual) -> is_mortal(individual))"
        fmls.append({"symbol": sym, "ascii": ascii_str, "json_structure": js})
    return {"formalizations": fmls, "confidence": 0.95, "reasoning": "test"}


class TestAutomaticFormEvaluator:
    """Test that form evaluator is automatically queued when all propositions are formalized"""

    def test_formalization_queues_form_evaluator_when_complete(self):
        """Test that formalization agent does not call queue_formal_evaluator_if_ready (handled elsewhere)"""
        agent = FormalizationAgent(coordinator)

        mock_existing_results = []

        mock_response = _mock_formalizations_response([
            ("1", "is_man", "socrates"),
            ("2", "is_man", None),  # universal: forall individual. (is_man -> is_mortal)
            ("3", "is_mortal", "socrates"),
        ])

        with patch('services.agents.agent_gpt_formalize') as mock_gpt, \
             patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results), \
             patch.object(coordinator, 'queue_formal_evaluator_if_ready') as mock_queue_form_eval:

            mock_gpt.call.return_value = json.dumps(mock_response)

            from schemas.agent_input import AgentInput, AgentData
            from schemas.step import Step

            agent_input = AgentInput(
                conversation_id='test_conversation',
                snapshot_id='test_snapshot',
                agent_data=AgentData(
                    assumptions=[],
                    argument=[
                        Step(symbol='1', proposition='Socrates is a man', justifiers=[], truth_score='1.0', content_validity='1.0', formal_validity='1.0'),
                        Step(symbol='2', proposition='All men are mortal', justifiers=[], truth_score='1.0', content_validity='1.0', formal_validity='1.0'),
                        Step(symbol='3', proposition='Socrates is mortal', justifiers=[], truth_score='1.0', content_validity='1.0', formal_validity='1.0'),
                    ],
                    latest_results=[],
                    target_type='proposition',
                    target_content='Socrates is mortal'
                ),
                file_ids=[]
            )

            result = agent.formalize_proposition(agent_input)

            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            # After normalization, formalizations use canonical symbols
            fmls = {f["symbol"]: f["ascii"] for f in result.result_content["formalizations"]}
            assert "1" in fmls
            assert "3" in fmls
            assert result.result_content["confidence"] == 0.95

            # Verify that queue_formal_evaluator_if_ready was NOT called by the FormalizationAgent
            mock_queue_form_eval.assert_not_called()

    def test_formalization_does_not_queue_form_evaluator_when_incomplete(self):
        """Test that formalization agent does not call queue_formal_evaluator_if_ready (handled elsewhere)"""
        agent = FormalizationAgent(coordinator)

        mock_existing_results = []

        mock_response = _mock_formalizations_response([
            ("1", "is_man", "socrates"),
            ("2", "is_man", None),
            ("3", "is_mortal", "socrates"),
        ])

        with patch('services.agents.agent_gpt_formalize') as mock_gpt, \
             patch.object(coordinator, 'get_conversation_results', return_value=mock_existing_results), \
             patch.object(coordinator, 'queue_formal_evaluator_if_ready') as mock_queue_form_eval:

            mock_gpt.call.return_value = json.dumps(mock_response)

            from schemas.agent_input import AgentInput, AgentData
            from schemas.step import Step

            agent_input = AgentInput(
                conversation_id='test_conversation',
                snapshot_id='test_snapshot',
                agent_data=AgentData(
                    assumptions=[],
                    argument=[
                        Step(symbol='1', proposition='Socrates is a man', justifiers=[], truth_score='1.0', content_validity='1.0', formal_validity='1.0'),
                        Step(symbol='2', proposition='All men are mortal', justifiers=[], truth_score='1.0', content_validity='1.0', formal_validity='1.0'),
                        Step(symbol='3', proposition='Socrates is mortal', justifiers=[], truth_score='1.0', content_validity='1.0', formal_validity='1.0'),
                    ],
                    latest_results=[],
                    target_type='proposition',
                    target_content='All men are mortal'
                ),
                file_ids=[]
            )

            result = agent.formalize_proposition(agent_input)

            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            fmls = result.result_content["formalizations"]
            assert len(fmls) == 3
            assert result.result_content["confidence"] == 0.95

            # Verify that queue_formal_evaluator_if_ready was NOT called by the FormalizationAgent
            mock_queue_form_eval.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
