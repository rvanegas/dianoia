import json
# import time
from typing import Dict, Any, List
from dataclasses import dataclass

# from services.conversation import gpt_justify, gpt_evaluate  # DISABLED: Old GPT instances - replaced by new agent system
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


class FormalEvaluatorAgent:
    """Agent that evaluates only the logical validity of formalized arguments"""
    
    def __init__(self, coordinator):
        if coordinator is None:
            raise ValueError("FormalEvaluatorAgent requires a coordinator")
        self.name = "form_evaluator"
        self.coordinator = coordinator

    def evaluate_propositions(self, agent_input: FilteredAgentInput) -> AgentResult:
        """Evaluate only the logical validity of formalized arguments"""
        try:
            # logger.info(f"FormalEvaluatorAgent starting task for conversation: {agent_input.conversation_id}")
            # logger.debug(f"FormalEvaluatorAgent starting task with data: {agent_input}")
            
            # Use FilteredAgentInput to focus on formal logic only
            filtered_input = FilteredAgentInput.for_formal_evaluation(agent_input)
            file_ids = filtered_input.file_ids
            payload = filtered_input.model_dump()
            arg_for_result = filtered_input.agent_data.argument
            assumptions_for_result = filtered_input.agent_data.assumptions
            
            # Pass the data directly to the agent
            evaluation_response = agent_gpt_evaluate_form.call(json.dumps(payload), file_ids)
            evaluation_result = json.loads(evaluation_response)
            
            # logger.info(f"FormalEvaluatorAgent completed")
            
            result = AgentResult(
                agent_type=self.name,
                operation="evaluate_propositions",
                result_content={
                    **evaluation_result,
                    "evaluation_mode": "formal_validity",
                    "argument": arg_for_result,
                    "assumptions": assumptions_for_result
                },
                target_metadata={
                    'target_type': 'argument'
                }
            )
            
            # logger.debug(f"FormalEvaluatorAgent task completed successfully. Output: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Formal evaluator agent error: {e}")
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
            # logger.debug(f"FormalEvaluatorAgent task failed. Output: {result}")
            return result
    
    def validate_formalizations(self, args) -> Dict[str, Any]:
        """Validate that all steps have endorsed formalizations"""
        return self._validate_formalizations(args)
    
    def create_and_queue_formal_evaluation_task(self, conversation_id: str, snapshot_id: str, args) -> Dict[str, Any]:
        """Create agent input and queue formal evaluation task"""
        from schemas.agent_input import AgentInput, AgentData
        
        # Create agent input for formal evaluation
        agent_input = AgentInput(
            conversation_id=conversation_id,
            snapshot_id=snapshot_id,
            agent_data=AgentData(
                assumptions=args.assumptions,
                argument=args.argument,
                latest_results=[],
                target_type='argument',
                target_content=None
            ),
            file_ids=args.file_ids,
            triggered_by='user_action',
            trigger_source='formalization_endorsed'
        )
        
        # Queue the formal evaluation task
        self.coordinator.queue_task(
            agent_type='form_evaluator',
            agent_input=agent_input
        )
        
        return {
            "message": "Formal evaluation agent triggered successfully",
            "conversation_id": conversation_id,
            "snapshot_id": snapshot_id,
            "validated_steps": len(args.argument + args.assumptions),
            "endorsed_formalizations": len(args.argument + args.assumptions)
        }
    
    def _validate_formalizations(self, args) -> Dict[str, Any]:
        """Validate that all steps have formalizations and all are endorsed"""
        all_steps = args.argument + args.assumptions
        
        # Check if any steps are missing formalizations
        steps_without_formalizations = [
            step.symbol for step in all_steps 
            if not step.formalization
        ]
        
        if steps_without_formalizations:
            return {
                "is_valid": False,
                "error_message": f"Steps missing formalizations: {steps_without_formalizations}",
                "total_steps": len(all_steps)
            }
        
        # Check if any formalizations are not endorsed
        unendorsed_formalizations = [
            step.symbol for step in all_steps 
            if step.formalization and not step.formalization.endorsed
        ]
        
        if unendorsed_formalizations:
            return {
                "is_valid": False,
                "error_message": f"Formalizations not endorsed: {unendorsed_formalizations}",
                "total_steps": len(all_steps)
            }
        
        return {
            "is_valid": True,
            "error_message": None,
            "total_steps": len(all_steps)
        }


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
    
    def formalize_proposition(self, agent_input: FilteredAgentInput) -> AgentResult:
        """Formalize a proposition into logical notation"""
        try:
            # logger.info(f"FormalizationAgent starting task for conversation: {agent_input.conversation_id}")
            # logger.debug(f"FormalizationAgent starting task with data: {agent_input}")
            
            # Use direct access for FilteredAgentInput
            file_ids = agent_input.file_ids
            payload = agent_input.model_dump()
            arg_for_result = agent_input.agent_data.argument
            assumptions_for_result = agent_input.agent_data.assumptions
            
            # Validate that we have argument data to formalize
            if not agent_input.agent_data.argument:
                raise ValueError("No argument provided for formalization")
            
            # Check if there are any steps that need formalization
            steps_needing_formalization = []
            for step in agent_input.agent_data.argument:
                if not step.formalization or not step.formalization.endorsed:
                    steps_needing_formalization.append(step)
            
            # If all steps have endorsed formalizations, return early
            if not steps_needing_formalization:
                result = AgentResult(
                    agent_type=self.name,
                    operation="formalize_proposition",
                    result_content={
                        "formalizations": [],
                        "definitions": {},
                        "confidence": 1.0,
                        "reasoning": "All steps already have endorsed formalizations - no new formalizations needed",
                        "formalization_mode": "proposition_to_logic",
                        "argument": arg_for_result,
                        "assumptions": assumptions_for_result
                    },
                    confidence=1.0,
                    reasoning="All steps have endorsed formalizations",
                    target_metadata={
                        'target_type': 'argument',
                        'target_content': agent_input.agent_data.target_content
                    }
                )
                return result
            
            # Keep all steps in the payload so the agent can see endorsed formalizations for consistency
            # The agent will only generate new formalizations for steps that need them
            
            # logger.debug(f"FormalizationAgent sending data: {payload}")
            
            # Pass the data directly to the agent
            formalization_response = agent_gpt_formalize.call(json.dumps(payload), file_ids)
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
                    **formalization_result,
                    "formalization_mode": "proposition_to_logic",
                    "argument": arg_for_result,
                    "assumptions": assumptions_for_result
                },
                target_metadata={
                    'target_type': 'argument',
                    'target_content': agent_input.agent_data.target_content
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
                    'target_type': 'argument',
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



