import json
# import time
from typing import Dict, Any, List
from dataclasses import dataclass

from services.conversation import gpt_justify, gpt_evaluate
from services.agent_prompts import agent_gpt_justify, agent_gpt_evaluate_content, agent_gpt_evaluate_form, agent_gpt_formalize
from schemas.agent_input import AgentInput, FilteredAgentInput

from core.utils import logger


@dataclass
class AgentResult:
    """Result from an agent operation"""
    agent_type: str
    operation: str
    result_content: Dict[str, Any]  # The actual output from the agent
    confidence: float = 0.0
    reasoning: str = ""
    target_metadata: Dict[str, Any] = None  # Metadata about what was targeted
    snapshot_id: str = ""  # Links result to specific snapshot
    
    def __post_init__(self):
        if self.target_metadata is None:
            self.target_metadata = {}


class ArgumentBuilderAgent:
    """Agent that builds arguments from content"""
    
    def __init__(self, coordinator):
        if coordinator is None:
            raise ValueError("ArgumentBuilderAgent requires a coordinator")
        self.name = "builder"
        self.coordinator = coordinator
    
    def build_argument(self, agent_input: AgentInput) -> AgentResult:
        """Build additional argument steps for a proposition with optional formalization guidance"""
        try:
            # logger.debug(f"ArgumentBuilderAgent starting task with data: {agent_input}")
            
            # Get file_ids from task data
            file_ids = agent_input.file_ids
            
            # Pass the data directly to the agent without taking it apart
            basic_response = agent_gpt_justify.call(json.dumps(agent_input.model_dump()), file_ids)
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
                result_content={
                    "proposition": agent_input.agent_data.target_content or '',
                    "location": "argument",
                    "justifications": justifications,
                    "total_justifications": len(justifications)
                },
                confidence=0.8,
                reasoning=f"Generated {len(justifications)} justification options",
                target_metadata={
                    'target_type': 'proposition',
                    'target_content': agent_input.agent_data.target_content or ''
                }
            )
            
            # logger.debug(f"ArgumentBuilderAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Builder agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="build_argument",
                result_content={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in argument building: {e}",
                target_metadata={
                    'target_type': 'proposition',
                    'target_content': agent_input.agent_data.target_content or ''
                }
            )
            # logger.debug(f"ArgumentBuilderAgent task failed. Output: {result}")
            return result
    

class ContentEvaluationAgent:
    """Agent that evaluates the truth and validity of argument propositions"""
    
    def __init__(self, coordinator):
        if coordinator is None:
            raise ValueError("ContentEvaluationAgent requires a coordinator")
        self.name = "content_evaluator"
        self.coordinator = coordinator
    
    def evaluate_propositions(self, agent_input: FilteredAgentInput) -> AgentResult:
        """Evaluate the truth and validity of argument propositions"""
        try:
            # logger.info(f"ContentEvaluationAgent starting task for conversation: {agent_input.conversation_id}")
            # logger.debug(f"ContentEvaluationAgent starting task with data: {agent_input}")
            
            # Use direct access for FilteredAgentInput
            file_ids = agent_input.file_ids
            payload = agent_input.model_dump()
            arg_for_result = agent_input.agent_data.argument
            assumptions_for_result = agent_input.agent_data.assumptions

            # Pass the data directly to the agent
            evaluation_response = agent_gpt_evaluate_content.call(json.dumps(payload), file_ids)
            evaluation_result = json.loads(evaluation_response)
            
            # logger.info(f"ContentEvaluationAgent completed")
            # if recommendations:
            #     logger.info(f"ContentEvaluationAgent provided {len(recommendations)} recommendations: {recommendations}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                result_content={
                    **evaluation_result,
                    "evaluation_mode": "content_truth_coherence",
                    "argument": arg_for_result,
                    "assumptions": assumptions_for_result
                },

                target_metadata={
                    'target_type': 'argument'
                }
            )
            
            # logger.debug(f"ContentEvaluationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Content evaluator agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                result_content={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in content evaluation: {e}",
                target_metadata={
                    'target_type': 'argument'
                }
            )
            # logger.debug(f"ContentEvaluationAgent task failed. Output: {result}")
            return result


class FormEvaluationAgent:
    """Agent that evaluates only the logical validity of formalized arguments"""
    
    def __init__(self, coordinator):
        if coordinator is None:
            raise ValueError("FormEvaluationAgent requires a coordinator")
        self.name = "form_evaluator"
        self.coordinator = coordinator
    
    def _get_formalizations_for_argument(self, agent_input: FilteredAgentInput) -> List[str]:
        """Get formalizations for all propositions in the argument"""
        argument = agent_input.agent_data.argument
        assumptions = agent_input.agent_data.assumptions
        
        # Extract formalizations from argument and assumption steps
        formalizations = []
        missing_formalizations = []
        
        # Check argument steps
        for step in argument:
            if step.formalization:
                formalizations.append(step.formalization)
            else:
                missing_formalizations.append(f"argument step {step.symbol}")
        
        # Check assumption steps
        for step in assumptions:
            if step.formalization:
                formalizations.append(step.formalization)
            else:
                missing_formalizations.append(f"assumption step {step.symbol}")
        
        if missing_formalizations:
            error_msg = f"Missing formalizations for steps: {missing_formalizations}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not formalizations:
            error_msg = "No formalizations found for form evaluation"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        return formalizations

    def evaluate_propositions(self, agent_input: FilteredAgentInput) -> AgentResult:
        """Evaluate only the logical validity of formalized arguments"""
        try:
            # logger.info(f"FormEvaluationAgent starting task for conversation: {agent_input.conversation_id}")
            # logger.debug(f"FormEvaluationAgent starting task with data: {agent_input}")
            
            # Use direct access for AgentInput
            file_ids = agent_input.file_ids
            formalizations = self._get_formalizations_for_argument(agent_input)
            assumptions_for_result = agent_input.agent_data.assumptions
            argument_for_result = agent_input.agent_data.argument
            
            # Create a clean data structure for the form evaluator - ONLY formalizations
            form_evaluation_data = {
                'formalizations': formalizations
            }
            
            # logger.debug(f"FormEvaluationAgent sending clean data: {form_evaluation_data}")
            
            # Pass the clean data to the agent for evaluation
            evaluation_response = agent_gpt_evaluate_form.call(json.dumps(form_evaluation_data), file_ids)
            evaluation_result = json.loads(evaluation_response)
            
            # Log key evaluation metrics
            proposition_count = len(evaluation_result.get("proposition_evaluations", []))
            argument_validity = evaluation_result.get("argument_validity", 0.0)
            logical_issues = evaluation_result.get("logical_issues", [])
            recommendations = evaluation_result.get("recommendations", [])
            
            # logger.info(f"FormEvaluationAgent completed - Propositions: {proposition_count}, Validity: {argument_validity:.2f}")
            # if logical_issues:
            #     logger.info(f"FormEvaluationAgent found {len(logical_issues)} logical issues: {logical_issues}")
            # if recommendations:
            #     logger.info(f"FormEvaluationAgent provided {len(recommendations)} recommendations: {recommendations}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                result_content={
                    "evaluation": evaluation_result,
                    "argument_validity": argument_validity,
                    "proposition_count": proposition_count,
                    "logical_issues": logical_issues,
                    "recommendations": recommendations,
                    "evaluation_mode": "formal_validity",
                    "argument": argument_for_result,
                    "assumptions": assumptions_for_result
                },
                confidence=argument_validity,
                reasoning=f"Evaluated {proposition_count} propositions for formal validity with {len(logical_issues)} issues identified",
                target_metadata={
                    'target_type': 'argument'
                }
            )
            
            # logger.info(f"FormEvaluationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Form evaluator agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                result_content={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in form evaluation: {e}",
                target_metadata={
                    'target_type': 'argument'
                }
            )
            # logger.debug(f"FormEvaluationAgent task failed. Output: {result}")
            return result


class FormalizationAgent:
    """Agent that formalizes propositions into logical notation"""
    
    def __init__(self, coordinator):
        if coordinator is None:
            raise ValueError("FormalizationAgent requires a coordinator")
        self.name = "formalizer"
        self.coordinator = coordinator
    
    def _get_existing_formalizations(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get existing formalizations for this conversation"""
        try:
            existing_results = self.coordinator.get_conversation_results(conversation_id)
            formalizations = []
            
            for result in existing_results:
                if result.get('agent_type') == 'formalizer':
                    formalizations.append(result.get('result_content', {}))
            
            return formalizations
            
        except Exception as e:
            logger.error(f"Error getting existing formalizations: {e}")
            return []
    
    def formalize_proposition(self, agent_input: AgentInput) -> AgentResult:
        """Formalize a proposition into logical notation"""
        try:
            # logger.info(f"FormalizationAgent starting task for conversation: {agent_input.conversation_id}")
            # logger.debug(f"FormalizationAgent starting task with data: {agent_input}")
            
            # Validate required data
            argument_data = agent_input.agent_data.argument
            if not argument_data:
                raise ValueError("FormalizationAgent requires argument data")
            
            # Get file_ids from task data
            file_ids = agent_input.file_ids
            
            # Get the proposition to formalize
            proposition = agent_input.agent_data.target_content
            if not proposition:
                raise ValueError("No proposition provided for formalization")
            
            # Get existing formalizations for context
            conversation_id = agent_input.conversation_id
            existing_formalizations = self._get_existing_formalizations(conversation_id)
            
            # Create formalization data
            formalization_data = {
                'proposition': proposition,
                'existing_formalizations': existing_formalizations,
                'argument_data': [step.model_dump() for step in argument_data]
            }
            
            # logger.debug(f"FormalizationAgent sending data: {formalization_data}")
            
            # Pass the data to the agent for formalization
            formalization_response = agent_gpt_formalize.call(json.dumps(formalization_data), file_ids)
            formalization_result = json.loads(formalization_response)
            
            # Extract formalization results
            formalization_obj = formalization_result.get("formalization", {})
            ascii_formalization = formalization_obj.get("ascii", "")
            json_formalization = formalization_obj.get("json", {})
            confidence = formalization_result.get("confidence", 0.0)
            reasoning = formalization_result.get("reasoning", "")
            
            # logger.info(f"FormalizationAgent completed - Proposition: '{proposition[:50]}...', Confidence: {confidence:.2f}")
            
            result = AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                result_content={
                    "proposition": proposition,
                    "ascii": ascii_formalization,
                    "json": json_formalization,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "formalization_mode": "proposition_to_logic"
                },
                confidence=confidence,
                reasoning=reasoning,
                target_metadata={
                    'target_type': 'proposition',
                    'target_content': proposition
                }
            )
            
            # logger.debug(f"FormalizationAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Formalization agent error: {e}")
            result = AgentResult(
                agent_type=self.name,
                operation="formalize_proposition",
                result_content={"error": str(e)},
                confidence=0.0,
                reasoning=f"Error in formalization: {e}",
                target_metadata={
                    'target_type': 'proposition',
                    'target_content': agent_input.agent_data.target_content or ''
                }
            )
            # logger.debug(f"FormalizationAgent task failed. Output: {result}")
            return result
    

class RewriterAgent:
    """Agent that recommends proposition rewrites, rephrasing, and splitting (STUB)"""
    
    def __init__(self, coordinator):
        if coordinator is None:
            raise ValueError("RewriterAgent requires a coordinator")
        self.name = "rewriter"
        self.coordinator = coordinator
    
    def rewrite_proposition(self, conversation_data: Dict[str, Any]) -> AgentResult:
        pass
