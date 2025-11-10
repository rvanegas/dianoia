import json
# import time
from typing import Dict, Any, List
from dataclasses import dataclass

from services.conversation import gpt_justify, gpt_evaluate
from services.agent_prompts import agent_gpt_justify
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
        """Build additional argument steps for a proposition with optional formalization guidance"""
        try:
            logger.debug(f"ArgumentBuilderAgent starting task with data: {conversation_data}")
            
            # Extract the argument structure from conversation data
            loc = conversation_data.get('loc', 'argument')
            index = conversation_data.get('index', 0)

            # Infer the proposition from loc and index
            proposition = self._get_proposition_at_location(conversation_data, loc, index)
            if not proposition:
                raise ValueError(f"No proposition found at {loc}[{index}]")
            
            # Create the argument structure for gpt_justify
            arg_data = {
                'assumptions': conversation_data.get('assumptions', []),
                'argument': conversation_data.get('argument', []),
                'counter_argument': conversation_data.get('counter_argument', []),
                'loc': loc,
                'index': index
            }
            
            # Generate justifications with optional formalization guidance
            justifications = []
            
            basic_prompt = {
                "proposition": proposition,
                "target_loc": loc,
                "target_index": index,
                "argument": conversation_data.get('argument', []),
                "counter_argument": conversation_data.get('counter_argument', []),
                "assumptions": conversation_data.get('assumptions', []),
            }
            basic_response = agent_gpt_justify.call(json.dumps(basic_prompt), conversation_data.get('file_ids'))
            basic_propositions = json.loads(basic_response)["propositions"]
            
            basic_justification = {
                "type": "basic",
                "propositions": basic_propositions,
                "used_formalization": None,
                "confidence": 0.8,
                "reasoning": "Generated justification without formalization guidance"
            }
            justifications.append(basic_justification)
            
            result = AgentResult(
                agent_type=self.name,
                operation="build_argument",
                data={
                    "justifications": justifications,
                    "target_loc": loc,
                    "target_index": index,
                    "total_justifications": len(justifications)
                },
                confidence=0.8,
                reasoning=f"Generated {len(justifications)} justification options (basic + formalization-guided)"
            )
            
            logger.debug(f"ArgumentBuilderAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Builder agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="build_argument",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in argument building: {e}"
            )
            logger.debug(f"ArgumentBuilderAgent task failed. Output: {result}")
            return result
    
    def _get_proposition_at_location(self, conversation_data: Dict[str, Any], loc: str, index: int) -> str:
        """Extract proposition from the specified location and index"""
        if loc == 'argument':
            argument = conversation_data.get('argument', [])
            if 0 <= index < len(argument):
                return argument[index].get('proposition', '')
        elif loc == 'counter_argument':
            counter_argument = conversation_data.get('counter_argument', [])
            if 0 <= index < len(counter_argument):
                return counter_argument[index].get('proposition', '')
        
        return None


class EvaluationAgent:
    """Agent that evaluates truth and validity of propositions (STUB)"""
    
    def __init__(self):
        self.name = "evaluator"
    
    def evaluate_propositions(self, conversation_data: Dict[str, Any]) -> AgentResult:
        pass

class FormalizationAgent:
    """Agent that suggests formalizations using core/logic.py constraints (STUB)"""
    
    def __init__(self):
        self.name = "formalizer"
    
    def formalize_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        pass

class RewriterAgent:
    """Agent that recommends proposition rewrites, rephrasing, and splitting (STUB)"""
    
    def __init__(self):
        self.name = "rewriter"
    
    def rewrite_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        pass

# Agent registry
AGENTS = {
    'builder': ArgumentBuilderAgent(),
    'evaluator': EvaluationAgent(),
    'formalizer': FormalizationAgent(),
    'rewriter': RewriterAgent()
} 
