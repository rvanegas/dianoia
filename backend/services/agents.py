import json
# import time
from typing import Dict, Any, List
from dataclasses import dataclass

from services.conversation import gpt_justify, gpt_evaluate
from services.agent_prompts import agent_gpt_justify, agent_gpt_evaluate, agent_gpt_formalize
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
            # logger.debug(f"ArgumentBuilderAgent starting task with data: {conversation_data}")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Queue formalizer tasks for unformalized propositions
            self._queue_formalizer_tasks(conversation_data)
            
            # Pass the data directly to the agent without taking it apart
            basic_response = agent_gpt_justify.call(json.dumps(conversation_data), file_ids)
            basic_propositions = json.loads(basic_response)["propositions"]
            
            basic_justification = {
                "type": "basic",
                "propositions": basic_propositions,
                "used_formalization": None,
                "confidence": 0.8,
                "reasoning": "Generated justification without formalization guidance"
            }
            justifications = [basic_justification]
            
            result = AgentResult(
                agent_type=self.name,
                operation="build_argument",
                data={
                    "justifications": justifications,
                    "total_justifications": len(justifications)
                },
                confidence=0.8,
                reasoning=f"Generated {len(justifications)} justification options and queued formalizer tasks"
            )
            
            # logger.debug(f"ArgumentBuilderAgent task completed successfully. Output: {result}")
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
            # logger.debug(f"ArgumentBuilderAgent task failed. Output: {result}")
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

    def _queue_formalizer_tasks(self, conversation_data: Dict[str, Any]):
        """Queue formalizer tasks for all unformalized propositions"""
        try:
            from services.agent_coordinator import coordinator

            # logger.debug(f"q1")
            
            # Get existing formalizations from agent results
            conversation_id = conversation_data.get('conversation_id')
            # logger.debug(f"Formalizer queueing - conversation_id: {conversation_id}")
            existing_results = coordinator.get_conversation_results(conversation_id)
            formalized_propositions = set()
            
            # logger.debug(f"q2")
            
            # Extract propositions that have already been formalized
            for result in existing_results:
                if result.get('agent_type') == 'formalizer':
                    proposition = result.get('data', {}).get('proposition')
                    if proposition:
                        formalized_propositions.add(proposition)
            
            # logger.debug(f"q3")
            
            # Get all propositions from the argument structure
            all_propositions = []
            
            # Add propositions from argument
            argument_data_raw = conversation_data.get('argument_data', '{}')
            
            # Parse argument_data if it's a JSON string
            if isinstance(argument_data_raw, str):
                try:
                    argument_data = json.loads(argument_data_raw)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse argument_data JSON: {e}")
                    argument_data = {}
            else:
                argument_data = argument_data_raw

            # logger.debug(f"q3.1, argument_data: {argument_data}")

            for step in argument_data.get('argument', []):
                if isinstance(step, dict) and 'proposition' in step:
                    all_propositions.append(step['proposition'])
            
            # logger.debug(f"q4")

            # Add propositions from counter_argument
            for step in argument_data.get('counter_argument', []):
                if isinstance(step, dict) and 'proposition' in step:
                    all_propositions.append(step['proposition'])
            
            # logger.debug(f"q5")

            # Add propositions from assumptions
            for step in argument_data.get('assumptions', []):
                if isinstance(step, dict) and 'proposition' in step:
                    all_propositions.append(step['proposition'])
            
            # logger.debug(f"q6")

            # Queue formalizer tasks for unformalized propositions
            file_ids = conversation_data.get('file_ids', [])
            
            # logger.debug(f"q7")

            unformalized_count = 0
            for proposition in all_propositions:
                if proposition not in formalized_propositions:
                    # logger.info(f"Queueing formalizer task for proposition: '{proposition[:50]}...'")
                    
                    # logger.debug(f"q8")

                    task_data = {
                        'proposition': proposition,
                        'argument_data': argument_data,
                        'file_ids': file_ids
                    }
                    
                    # logger.debug(f"q9")

                    coordinator.queue_task(
                        agent_type='formalizer',
                        conversation_id=conversation_id,
                        data=task_data
                    )
                    
                    # logger.debug(f"q10")

                    # logger.debug(f"Queued formalizer task for proposition: {proposition}")

                    # logger.debug(f"q11")

                    unformalized_count += 1
            
            # logger.info(f"Queued {unformalized_count} formalizer tasks for unformalized propositions")

            # logger.debug(f"q12")

        except Exception as e:
            logger.error(f"Error queueing formalizer tasks: {e}")


class EvaluationAgent:
    """Agent that evaluates truth and validity of propositions"""
    
    def __init__(self):
        self.name = "evaluator"
    
    def evaluate_propositions(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Evaluate the truth, validity, and soundness of propositions and arguments"""
        try:
            # logger.info(f"EvaluationAgent starting task for conversation: {conversation_data.get('conversation_id', 'unknown')}")
            # logger.debug(f"EvaluationAgent starting task with data: {conversation_data}")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Pass the data directly to the agent for evaluation
            evaluation_response = agent_gpt_evaluate.call(json.dumps(conversation_data), file_ids)
            evaluation_result = json.loads(evaluation_response)
            
            # Log key evaluation metrics
            proposition_count = len(evaluation_result.get("proposition_evaluations", []))
            argument_validity = evaluation_result.get("argument_validity", 0.0)
            logical_issues = evaluation_result.get("logical_issues", [])
            recommendations = evaluation_result.get("recommendations", [])
            
            # logger.info(f"EvaluationAgent completed - Propositions: {proposition_count}, Validity: {argument_validity:.2f}")
            # if logical_issues:
            #     logger.info(f"EvaluationAgent found {len(logical_issues)} logical issues: {logical_issues}")
            # if recommendations:
            #     logger.info(f"EvaluationAgent provided {len(recommendations)} recommendations: {recommendations}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={
                    "evaluation": evaluation_result,
                    "proposition_count": proposition_count,
                    "argument_validity": argument_validity,
                    "logical_issues": logical_issues,
                    "recommendations": recommendations
                },
                confidence=argument_validity,
                reasoning=f"Evaluated {proposition_count} propositions with {len(logical_issues)} issues identified"
            )
            
            # logger.debug(f"EvaluationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Evaluator agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in proposition evaluation: {e}"
            )
            # logger.debug(f"EvaluationAgent task failed. Output: {result}")
            return result

class FormalizationAgent:
    """Agent that formalizes natural language propositions into formal logic"""
    
    def __init__(self):
        self.name = "formalizer"
    
    def formalize_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Formalize a natural language proposition into formal logic"""
        try:
            # logger.info(f"FormalizationAgent starting task for conversation: {conversation_data.get('conversation_id', 'unknown')}")
            # logger.debug(f"FormalizationAgent starting task with data: {conversation_data}")
            
            # Extract the proposition to formalize
            proposition = conversation_data.get('proposition', '')
            if not proposition:
                raise ValueError("No proposition provided for formalization")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Prepare data for the formalizer
            formalization_data = {
                'proposition': proposition,
                'argument_data': conversation_data.get('argument_data', {}),
                'file_ids': file_ids
            }
            
            # Call the formalizer agent
            formalization_response = agent_gpt_formalize.call(json.dumps(formalization_data), file_ids)
            formalization_result = json.loads(formalization_response)
            
            # Extract formalization details
            formalization = formalization_result.get('formalization', {})
            confidence = formalization_result.get('confidence', 0.0)
            reasoning = formalization_result.get('reasoning', '')
            
            # logger.info(f"FormalizationAgent completed - Proposition: '{proposition[:50]}...', Confidence: {confidence:.2f}")
            # logger.debug(f"Formalization result: {formalization_result}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                data={
                    "proposition": proposition,
                    "formalization": formalization,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "ascii": formalization.get('ascii', ''),
                    "json": {}  # Empty JSON for now
                },
                confidence=confidence,
                reasoning=reasoning
            )
            
            # logger.debug(f"FormalizationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Formalizer agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                data={
                    "proposition": conversation_data.get('proposition', ''),
                    "error": str(e)
                },
                confidence=0.0,
                reasoning=f"Error in proposition formalization: {e}"
            )
            # logger.debug(f"FormalizationAgent task failed. Output: {result}")
            return result

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
