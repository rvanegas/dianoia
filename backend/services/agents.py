import json
# import time
from typing import Dict, Any, List
from dataclasses import dataclass

from services.conversation import gpt_justify, gpt_evaluate
from services.agent_prompts import agent_gpt_justify, agent_gpt_evaluate_content, agent_gpt_evaluate_form, agent_gpt_formalize
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
    
    def __init__(self, coordinator=None):
        self.name = "builder"
        self.coordinator = coordinator
    
    def build_argument(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Build additional argument steps for a proposition with optional formalization guidance"""
        try:
            # logger.debug(f"ArgumentBuilderAgent starting task with data: {conversation_data}")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Queue formalizer task for the specific proposition this builder is working on
            self._queue_formalizer_task_for_proposition(conversation_data)
            
            # Queue content evaluator task to evaluate the argument
            self._queue_content_evaluator_task(conversation_data)
            
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
                    "proposition": conversation_data.get('proposition', ''),
                    "location": conversation_data.get('location', ''),
                    "justifications": justifications,
                    "total_justifications": len(justifications)
                },
                confidence=0.8,
                reasoning=f"Generated {len(justifications)} justification options and queued formalizer and content evaluator tasks"
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
                item = argument[index]
                if isinstance(item, dict):
                    return item.get('proposition', '')
                else:
                    return str(item)
        elif loc == 'counter_argument':
            counter_argument = conversation_data.get('counter_argument', [])
            if 0 <= index < len(counter_argument):
                item = counter_argument[index]
                if isinstance(item, dict):
                    return item.get('proposition', '')
                else:
                    return str(item)
        
        return None

    def _queue_formalizer_task_for_proposition(self, conversation_data: Dict[str, Any]):
        """Queue formalizer task for the proposition this builder is working on"""
        conversation_id = conversation_data['conversation_id']
        proposition = conversation_data['proposition']
        
        # Get existing formalizations to avoid duplicate work
        existing_results = self.coordinator.get_conversation_results(conversation_id)
        formalized_propositions = set()
        for result in existing_results:
            if result.get('agent_type') == 'formalizer':
                existing_proposition = result.get('data', {}).get('proposition')
                if existing_proposition:
                    formalized_propositions.add(existing_proposition)
        
        # Only queue formalizer task if this proposition hasn't been formalized yet
        if proposition not in formalized_propositions:
            logger.info(f"Queueing formalizer task for proposition: '{proposition[:50]}...'")
            
            task_data = {
                'proposition': proposition,
                'argument_data': conversation_data.get('argument_data', {}),
                'file_ids': conversation_data.get('file_ids', [])
            }
            
            self.coordinator.queue_task(
                agent_type='formalizer',
                conversation_id=conversation_id,
                data=task_data
            )
            
            logger.info(f"Queued formalizer task for proposition: {proposition}")
        else:
            logger.info(f"Proposition already formalized: {proposition}")
    
    def _queue_content_evaluator_task(self, conversation_data: Dict[str, Any]):
        """Queue content evaluator task for the argument"""
        conversation_id = conversation_data['conversation_id']
        
        # Get existing content evaluations from agent results
        existing_results = self.coordinator.get_conversation_results(conversation_id)
        content_evaluations = [r for r in existing_results if r.get('agent_type') == 'content_evaluator']
        
        # Only queue content evaluator task if there isn't already one
        if not content_evaluations:
            logger.info(f"Queueing content evaluator task for conversation: {conversation_id}")
            
            task_data = {
                'argument': conversation_data.get('argument', []),
                'thesis': conversation_data.get('thesis', ''),
                'counter_thesis': conversation_data.get('counter_thesis', ''),
                'assumptions': conversation_data.get('assumptions', []),
                'file_ids': conversation_data.get('file_ids', [])
            }
            
            self.coordinator.queue_task(
                agent_type='content_evaluator',
                conversation_id=conversation_id,
                data=task_data
            )
            
            logger.info(f"Queued content evaluator task for conversation: {conversation_id}")
        else:
            logger.info(f"Content evaluator already exists for conversation: {conversation_id}")


class ContentEvaluationAgent:
    """Agent that evaluates the truth and validity of argument propositions"""
    
    def __init__(self, coordinator=None):
        self.name = "content_evaluator"
        self.coordinator = coordinator
    
    def evaluate_propositions(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Evaluate the truth and validity of argument propositions"""
        try:
            logger.info(f"ContentEvaluationAgent starting task for conversation: {conversation_data['conversation_id']}")
            logger.debug(f"ContentEvaluationAgent starting task with data: {conversation_data}")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Pass the data directly to the agent
            evaluation_response = agent_gpt_evaluate_content.call(json.dumps(conversation_data), file_ids)
            evaluation_result = json.loads(evaluation_response)
            
            # Log key evaluation metrics
            proposition_count = len(evaluation_result.get("proposition_evaluations", []))
            overall_truth_score = evaluation_result.get("overall_truth_score", 0.0)
            truth_issues = evaluation_result.get("truth_issues", [])
            recommendations = evaluation_result.get("recommendations", [])
            
            logger.info(f"ContentEvaluationAgent completed - Propositions: {proposition_count}, Truth Score: {overall_truth_score:.2f}")
            if truth_issues:
                logger.info(f"ContentEvaluationAgent found {len(truth_issues)} truth issues: {truth_issues}")
            if recommendations:
                logger.info(f"ContentEvaluationAgent provided {len(recommendations)} recommendations: {recommendations}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={
                    "evaluation": evaluation_result,
                    "proposition_count": proposition_count,
                    "overall_truth_score": overall_truth_score,
                    "truth_issues": truth_issues,
                    "recommendations": recommendations,
                    "evaluation_mode": "content_truth",
                    "argument": conversation_data['argument'],
                    "thesis": conversation_data['thesis'],
                    "counter_thesis": conversation_data['counter_thesis'],
                    "assumptions": conversation_data['assumptions']
                },
                confidence=overall_truth_score,
                reasoning=f"Evaluated {proposition_count} propositions for truth with {len(truth_issues)} issues identified"
            )
            
            # logger.debug(f"ContentEvaluationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Content evaluator agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in content evaluation: {e}"
            )
            # logger.debug(f"ContentEvaluationAgent task failed. Output: {result}")
            return result


class FormEvaluationAgent:
    """Agent that evaluates only the logical validity of formalized arguments"""
    
    def __init__(self, coordinator=None):
        self.name = "form_evaluator"
        self.coordinator = coordinator
    
    def _get_formalizations_for_argument(self, conversation_data: Dict[str, Any]) -> List[str]:
        """Get formalizations for all propositions in the argument"""
        conversation_id = conversation_data['conversation_id']
        argument = conversation_data['argument']
        
        if not argument:
            return []
        
        # Get existing results
        existing_results = self.coordinator.get_conversation_results(conversation_id)
        
        # Map propositions to their formalizations
        formalizations = []
        for proposition in argument:
            # Find the formalization for this proposition
            formalization = None
            for result in existing_results:
                if (result.get('agent_type') == 'formalizer' and 
                    result.get('data', {}).get('proposition') == proposition):
                    formalization = result.get('data', {}).get('ascii')
                    break
            
            if formalization:
                formalizations.append(formalization)
            else:
                # If no formalization found, use the original proposition
                formalizations.append(proposition)
        
        return formalizations
    
    def evaluate_propositions(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Evaluate only the logical validity of formalized arguments"""
        try:
            logger.info(f"FormEvaluationAgent starting task for conversation: {conversation_data['conversation_id']}")
            logger.debug(f"FormEvaluationAgent starting task with data: {conversation_data}")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Add formalizations to the data
            formalizations = self._get_formalizations_for_argument(conversation_data)
            conversation_data['formalizations'] = formalizations
            
            # Create a clean data structure for the form evaluator - ONLY formalizations
            form_evaluation_data = {
                'formalizations': formalizations
            }
            
            logger.debug(f"FormEvaluationAgent sending clean data: {form_evaluation_data}")
            
            # Pass the clean data to the agent for evaluation
            evaluation_response = agent_gpt_evaluate_form.call(json.dumps(form_evaluation_data), file_ids)
            evaluation_result = json.loads(evaluation_response)
            
            # Log key evaluation metrics
            proposition_count = len(evaluation_result.get("proposition_evaluations", []))
            argument_validity = evaluation_result.get("argument_validity", 0.0)
            logical_issues = evaluation_result.get("logical_issues", [])
            recommendations = evaluation_result.get("recommendations", [])
            
            logger.info(f"FormEvaluationAgent completed - Propositions: {proposition_count}, Validity: {argument_validity:.2f}")
            if logical_issues:
                logger.info(f"FormEvaluationAgent found {len(logical_issues)} logical issues: {logical_issues}")
            if recommendations:
                logger.info(f"FormEvaluationAgent provided {len(recommendations)} recommendations: {recommendations}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={
                    "evaluation": evaluation_result,
                    "proposition_count": proposition_count,
                    "argument_validity": argument_validity,
                    "logical_issues": logical_issues,
                    "recommendations": recommendations,
                    "evaluation_mode": "formal_validity",
                    "argument": conversation_data['argument'],
                    "thesis": conversation_data['thesis'],
                    "counter_thesis": conversation_data['counter_thesis'],
                    "assumptions": conversation_data['assumptions']
                },
                confidence=argument_validity,
                reasoning=f"Evaluated {proposition_count} propositions for formal validity with {len(logical_issues)} issues identified"
            )
            
            # logger.debug(f"FormEvaluationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Form evaluator agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in form evaluation: {e}"
            )
            # logger.debug(f"FormEvaluationAgent task failed. Output: {result}")
            return result


class FormalizationAgent:
    """Agent that formalizes propositions into logical notation"""
    
    def __init__(self, coordinator=None):
        self.name = "formalizer"
        self.coordinator = coordinator
    
    def _get_existing_formalizations(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get existing formalizations for this conversation"""
        try:
            if not self.coordinator:
                return []
                
            existing_results = self.coordinator.get_conversation_results(conversation_id)
            formalizations = []
            
            for result in existing_results:
                if result.get('agent_type') == 'formalizer':
                    formalizations.append(result.get('data', {}))
            
            return formalizations
            
        except Exception as e:
            logger.error(f"Error getting existing formalizations: {e}")
            return []
    
    def formalize_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        """Formalize a proposition into logical notation"""
        try:
            logger.info(f"FormalizationAgent starting task for conversation: {conversation_data['conversation_id']}")
            logger.debug(f"FormalizationAgent starting task with data: {conversation_data}")
            
            # Get file_ids from task data
            file_ids = conversation_data.get('file_ids', [])
            
            # Get the proposition to formalize
            proposition = conversation_data.get('proposition', '')
            if not proposition:
                raise ValueError("No proposition provided for formalization")
            
            # Get existing formalizations for context
            conversation_id = conversation_data.get('conversation_id')
            existing_formalizations = self._get_existing_formalizations(conversation_id)
            
            # Create formalization data
            formalization_data = {
                'proposition': proposition,
                'existing_formalizations': existing_formalizations,
                'argument_data': conversation_data.get('argument_data', {})
            }
            
            logger.debug(f"FormalizationAgent sending data: {formalization_data}")
            
            # Pass the data to the agent for formalization
            formalization_response = agent_gpt_formalize.call(json.dumps(formalization_data), file_ids)
            formalization_result = json.loads(formalization_response)
            
            # Extract formalization results
            ascii_formalization = formalization_result.get("ascii", "")
            latex_formalization = formalization_result.get("latex", "")
            confidence = formalization_result.get("confidence", 0.0)
            reasoning = formalization_result.get("reasoning", "")
            
            logger.info(f"FormalizationAgent completed - Proposition: '{proposition[:50]}...', Confidence: {confidence:.2f}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                data={
                    "proposition": proposition,
                    "ascii": ascii_formalization,
                    "latex": latex_formalization,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "formalization_mode": "proposition_to_logic"
                },
                confidence=confidence,
                reasoning=reasoning
            )
            
            # Check if we should queue form evaluator after formalization
            self._check_and_queue_form_evaluator(conversation_data)
            
            # logger.debug(f"FormalizationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Formalization agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in formalization: {e}"
            )
            # logger.debug(f"FormalizationAgent task failed. Output: {result}")
            return result
    
    def _check_and_queue_form_evaluator(self, conversation_data: Dict[str, Any]):
        """Check if all propositions are formalized and queue form evaluator if so"""
        try:
            if not self.coordinator:
                logger.warning("No coordinator available for queueing form evaluator")
                return
                
            conversation_id = conversation_data.get('conversation_id')
            if not conversation_id:
                logger.warning("No conversation_id found in formalizer task data")
                return
            
            # Get the argument data
            argument_data = conversation_data.get('argument_data', {})
            argument = argument_data.get('argument', [])
            if not argument:
                logger.warning("No argument found in formalizer task data")
                return
            
            # Extract proposition texts from the argument
            argument_propositions = []
            
            # Debug: log the argument type and content
            # logger.debug(f"Argument type: {type(argument)}, content: {argument}")
            
            # Handle different argument formats
            if isinstance(argument, str):
                # If argument is a string, treat it as a single proposition
                argument_propositions = [argument]
            elif isinstance(argument, list):
                # If argument is a list, extract propositions from each step
                for step in argument:
                    if isinstance(step, dict):
                        proposition = step.get('proposition', '')
                    else:
                        proposition = str(step)
                    if proposition:
                        argument_propositions.append(proposition)
            else:
                # Fallback: convert to string and treat as single proposition
                argument_propositions = [str(argument)]
            
            # Get existing formalizations
            existing_results = self.coordinator.get_conversation_results(conversation_id)
            formalized_propositions = set()
            for result in existing_results:
                if result.get('agent_type') == 'formalizer':
                    existing_proposition = result.get('data', {}).get('proposition')
                    if existing_proposition:
                        formalized_propositions.add(existing_proposition)
            
            # Add the current proposition being formalized
            current_proposition = conversation_data.get('proposition', '')
            if current_proposition:
                formalized_propositions.add(current_proposition)
            
            # Check if all propositions are now formalized
            argument_propositions_set = set(argument_propositions)
            if argument_propositions_set.issubset(formalized_propositions):
                # logger.info(f"All propositions formalized, queueing form evaluator")
                # Queue form evaluator task
                task_data = {
                    'argument': argument_propositions,
                    'thesis': argument_data.get('thesis', ''),
                    'counter_thesis': argument_data.get('counter_thesis', ''),
                    'assumptions': argument_data.get('assumptions', []),
                    'file_ids': conversation_data.get('file_ids', [])
                }
                
                self.coordinator.queue_task(
                    agent_type='form_evaluator',
                    conversation_id=conversation_id,
                    data=task_data
                )
                
                # logger.info(f"Queued form evaluator task for conversation {conversation_id}")
            else:
                # logger.info(f"Not all propositions formalized yet. Formalized: {formalized_propositions}, Needed: {argument_propositions_set}")
                pass
            
        except Exception as e:
            logger.error(f"Error checking and queueing form evaluator: {e}")
    
    def _cleanup_invalid_form_evaluator_results(self, conversation_data: Dict[str, Any]):
        """Clean up form evaluator results that are no longer valid"""
        try:
            if not self.coordinator:
                logger.warning("No coordinator available for cleanup")
                return
                
            conversation_id = conversation_data.get('conversation_id')
            if not conversation_id:
                return
            
            # Get the argument from the conversation data
            argument_data = conversation_data.get('argument_data', {})
            
            argument = argument_data.get('argument', [])
            if not argument:
                return
            
            # Extract proposition texts from the argument
            argument_propositions = []
            
            # Debug: log the argument type and content
            # logger.debug(f"Argument type: {type(argument)}, content: {argument}")
            
            # Handle different argument formats
            if isinstance(argument, str):
                # If argument is a string, treat it as a single proposition
                argument_propositions = [argument]
            elif isinstance(argument, list):
                # If argument is a list, extract propositions from each step
                for step in argument:
                    if isinstance(step, dict):
                        proposition = step.get('proposition', '')
                    else:
                        proposition = str(step)
                    if proposition:
                        argument_propositions.append(proposition)
            else:
                # Fallback: convert to string and treat as single proposition
                argument_propositions = [str(argument)]
            
            # Check if all propositions are formalized
            if not self.coordinator.check_formalization_completion(conversation_id, argument_propositions):
                # If not all propositions are formalized, clean up form evaluator results
                results = self.coordinator.result_manager.get_results(conversation_id)
                results[:] = [
                    result for result in results
                    if result.get('agent_type') != 'form_evaluator'
                ]
                # logger.info(f"Cleaned up invalid form evaluator results for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up invalid form evaluator results: {e}")


class RewriterAgent:
    """Agent that recommends proposition rewrites, rephrasing, and splitting (STUB)"""
    
    def __init__(self, coordinator=None):
        self.name = "rewriter"
        self.coordinator = coordinator
    
    def rewrite_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        pass

# Agent registry - agents are created by coordinator with dependency injection 
