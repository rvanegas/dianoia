import json
# import time
from typing import Dict, Any, List
from dataclasses import dataclass

from services.conversation import gpt_justify, gpt_evaluate
from core.utils import logger


@dataclass
class AgentResult:
    """Result from an agent operation"""
    agent_type: str
    operation: str
    data: Dict[str, Any]
    confidence: float = 0.0
    reasoning: str = ""


class ArgumentBuilderAgent:
    """Agent that builds complex multi-step arguments"""

    def __init__(self):
        self.name = "builder"

    def build_argument(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Build additional argument steps for a proposition"""
        try:
            # Extract the argument structure from conversation data
            # This mimics the existing ai_justify functionality
            loc = conversation_data.get('loc', 'argument')
            index = conversation_data.get('index', 0)
            
            # Create the argument structure for gpt_justify
            arg_data = {
                'assumptions': conversation_data.get('assumptions', []),
                'argument': conversation_data.get('argument', []),
                'counter_argument': conversation_data.get('counter_argument', []),
                'loc': loc,
                'index': index
            }
            
            # Call the existing gpt_justify function
            response = gpt_justify.call(json.dumps(arg_data), conversation_data.get('file_ids'))
            new_propositions = json.loads(response)["propositions"]
            
            # Clean and process the propositions
            cleaned_propositions = []
            for prop in new_propositions:
                # Clean citations (similar to existing clean_citations function)
                cleaned = self._clean_citations(prop)
                cleaned_propositions.append(cleaned)
            
            return AgentResult(
                agent_type=self.name,
                operation="build_argument",
                data={
                    "new_propositions": cleaned_propositions,
                    "target_loc": loc,
                    "target_index": index,
                    "reasoning": f"Generated {len(cleaned_propositions)} new propositions to support the argument"
                },
                confidence=0.8,
                reasoning="Used existing gpt_justify to generate supporting propositions"
            )
            
        except Exception as e:
            logger.error(f"Builder agent error: {e}")
            return AgentResult(
                agent_type=self.name,
                operation="build_argument",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in argument building: {e}"
            )
    
    def _clean_citations(self, proposition: str) -> str:
        """Clean citations from propositions (simplified version)"""
        # Remove common citation patterns
        import re
        # Remove citations like [1], [Smith 2020], etc.
        cleaned = re.sub(r'\[[^\]]*\]', '', proposition)
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned


class EvaluationAgent:
    """Agent that evaluates truth and validity of propositions"""
    
    def __init__(self):
        self.name = "evaluator"
    
    def evaluate_propositions(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Evaluate truth and validity of propositions"""
        try:
            # Extract argument structure
            assumptions = conversation_data.get('assumptions', [])
            argument = conversation_data.get('argument', [])
            counter_argument = conversation_data.get('counter_argument', [])
            
            # Evaluate main argument
            main_evaluations = []
            if argument:
                main_evaluations = self._evaluate_argument(assumptions, argument)
            
            # Evaluate counter argument
            counter_evaluations = []
            if counter_argument:
                counter_evaluations = self._evaluate_argument(assumptions, counter_argument)
            
            return AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={
                    "main_argument_evaluations": main_evaluations,
                    "counter_argument_evaluations": counter_evaluations,
                    "assumptions": assumptions
                },
                confidence=0.9,
                reasoning="Evaluated truth and validity using existing gpt_evaluate function"
            )
            
        except Exception as e:
            logger.error(f"Evaluator agent error: {e}")
            return AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in evaluation: {e}"
            )

    def _evaluate_argument(self, assumptions: List, argument: List) -> List[Dict]:
        """Evaluate a single argument using gpt_evaluate"""
        evaluations = []

        for i, step in enumerate(argument):
            if hasattr(step, 'justifiers') and step.justifiers:
                # Create subargument for evaluation
                subarg = [s for s in argument if s.symbol in step.justifiers]
                subarg.append(step)

                # Prepare data for gpt_evaluate
                eval_data = {
                    "assumptions": [s.json() if hasattr(s, 'json') else s for s in assumptions],
                    "argument": [s.json() if hasattr(s, 'json') else s for s in subarg]
                }

                try:
                    response = gpt_evaluate.call(json.dumps(eval_data), [])
                    evaluation = json.loads(response)

                    evaluations.append({
                        "step_symbol": step.symbol if hasattr(step, 'symbol') else f"step_{i}",
                        "truth_values": evaluation.get("truth", []),
                        "validity": evaluation.get("valid", "0.0"),
                        "premises": [s.symbol if hasattr(s, 'symbol') else str(s) for s in subarg[:-1]],
                        "conclusion": step.symbol if hasattr(step, 'symbol') else str(step)
                    })
                except Exception as e:
                    logger.error(f"Evaluation error for step {i}: {e}")
                    evaluations.append({
                        "step_symbol": step.symbol if hasattr(step, 'symbol') else f"step_{i}",
                        "error": str(e)
                    })
        
        return evaluations


class FormalizationAgent:
    """Agent that suggests formalizations using core/logic.py constraints"""
    
    def __init__(self):
        self.name = "formalizer"
    
    def formalize_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Suggest formalizations for propositions"""
        try:
            # For now, return a placeholder that will be enhanced with core/logic.py
            # This is a foundation for the formalization workflow
            proposition = conversation_data.get('proposition', '')
            
            # Placeholder formalization options
            formalizations = [
                {
                    "formula": "P(a)",
                    "unicode": "P(a)",
                    "reasoning": "Simple predicate application",
                    "confidence": 0.6
                },
                {
                    "formula": "forall x. P(x)",
                    "unicode": "∀x. P(x)",
                    "reasoning": "Universal quantification",
                    "confidence": 0.4
                }
            ]
            
            return AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                data={
                    "original_proposition": proposition,
                    "formalizations": formalizations,
                    "reasoning": "Generated formalization options (placeholder - will integrate with core/logic.py)"
                },
                confidence=0.7,
                reasoning="Generated formalization options for user selection"
            )
            
        except Exception as e:
            logger.error(f"Formalizer agent error: {e}")
            return AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in formalization: {e}"
            )


# Agent registry
AGENTS = {
    'builder': ArgumentBuilderAgent(),
    'evaluator': EvaluationAgent(),
    'formalizer': FormalizationAgent()
} 