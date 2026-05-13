import pytest
import json
from unittest.mock import patch
from services.agents import FormalizationAgent
from services.agent_coordinator import coordinator
from schemas.step import Step
from schemas.agent_input import AgentInput, AgentData, FilteredAgentInput


class TestFormalizationAgent:
    """Test that the FormalizationAgent works correctly with the new structure"""

    def test_formalization_agent(self):
        """Test that formalization agent normalizes LLM output to canonical symbols"""
        agent = FormalizationAgent(coordinator)

        # Mock LLM response uses semantic names and core/logic.py JSON format
        mock_response = {
            "formalizations": [
                {
                    "symbol": "1",
                    "ascii": "is_man(socrates)",
                    "json_structure": json.dumps({
                        "type": "predicate", "pred_const": "is_man",
                        "args": [{"type": "constant", "name": "socrates"}]
                    })
                },
                {
                    "symbol": "2",
                    "ascii": "forall individual. (is_man(individual) implies is_mortal(individual))",
                    "json_structure": json.dumps({
                        "type": "quantifier", "quant": "forall",
                        "vars": [{"type": "variable", "name": "individual"}],
                        "body": {
                            "type": "connective", "op": "implies",
                            "args": [
                                {"type": "predicate", "pred_const": "is_man",
                                 "args": [{"type": "variable", "name": "individual"}]},
                                {"type": "predicate", "pred_const": "is_mortal",
                                 "args": [{"type": "variable", "name": "individual"}]}
                            ]
                        }
                    })
                },
                {
                    "symbol": "3",
                    "ascii": "is_mortal(socrates)",
                    "json_structure": json.dumps({
                        "type": "predicate", "pred_const": "is_mortal",
                        "args": [{"type": "constant", "name": "socrates"}]
                    })
                }
            ],
            "confidence": 0.9,
            "reasoning": "Classic syllogism formalized with semantic predicate names"
        }

        with patch('services.agents.agent_gpt_formalize') as mock_gpt:
            mock_gpt.call.return_value = json.dumps(mock_response)

            agent_data = AgentData(
                assumptions=[],
                argument=[
                    Step(symbol="1", proposition="Socrates is a man", justifiers=[], truth_score="", valid=""),
                    Step(symbol="2", proposition="All men are mortal", justifiers=[], truth_score="", valid=""),
                    Step(symbol="3", proposition="Socrates is mortal", justifiers=["1", "2"], truth_score="", valid="")
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

            filtered_input = FilteredAgentInput.for_formalization(agent_input)
            result = agent.formalize_proposition(filtered_input)

            assert result.agent_type == "formalizer"
            assert result.operation == "formalize_proposition"
            assert result.result_content["formalization_mode"] == "proposition_to_logic"
            assert len(result.result_content["formalizations"]) == 3

            # Python normalizes: is_man → P (first appearance), is_mortal → Q, socrates → a
            fmls = {f["symbol"]: f["ascii"] for f in result.result_content["formalizations"]}
            assert fmls["1"] == "Pa"
            assert fmls["3"] == "Qa"
            assert "forall x." in fmls["2"]

            # Definitions are Python-generated from semantic names
            preds = {p["symbol"]: p["value"] for p in result.result_content["definitions"]["predicates"]}
            consts = {c["symbol"]: c["value"] for c in result.result_content["definitions"]["constants"]}
            assert preds["P"] == "is_man"
            assert preds["Q"] == "is_mortal"
            assert consts["a"] == "socrates"

            assert result.result_content["confidence"] == 0.9
            assert result.target_metadata["target_type"] == "argument"
            assert result.target_metadata["target_content"] is None


if __name__ == "__main__":
    pytest.main([__file__])
