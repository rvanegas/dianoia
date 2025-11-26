import threading
import time
import uuid
from queue import Queue
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from core.utils import logger
from services.agents import ArgumentBuilderAgent, ContentEvaluationAgent, FormEvaluationAgent, FormalizationAgent, RewriterAgent

# TTL configuration
AGENT_RESULT_TTL_SECONDS = 3 * 24 * 60 * 60  # 3 days in seconds


@dataclass
class AgentTask:
    """Represents a task for an agent to process"""
    id: str
    agent_type: str  # 'builder', 'content_evaluator', 'form_evaluator', 'formalizer', 'rewriter'
    conversation_id: str
    data: Dict[str, Any]
    status: str = 'pending'  # 'pending', 'running', 'completed', 'failed'
    priority: int = 0
    created_at: float = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class AgentResultManager:
    """Manages agent results with disciplined cleanup and TTL maintenance"""
    
    def __init__(self):
        self.results_by_conversation: Dict[str, List[Dict[str, Any]]] = {}
        self.conversation_timestamps: Dict[str, float] = {}  # Track last activity per conversation
    
    def add_result(self, conversation_id: str, result: Dict[str, Any]):
        """Add a new result and clean up outdated ones"""
        if conversation_id not in self.results_by_conversation:
            self.results_by_conversation[conversation_id] = []
        
        # Clean up outdated results before adding the new one
        self._cleanup_outdated_results(conversation_id, result)
        
        # Check if this form evaluator result should be added
        if result.get('agent_type') == 'form_evaluator':
            if not self._should_add_form_evaluator_result(conversation_id, result):
                # Don't add the result if formalization is incomplete
                return
        
        # Add the new result and update conversation timestamp
        self.results_by_conversation[conversation_id].append(result)
        self.conversation_timestamps[conversation_id] = time.time()
    
    def _cleanup_outdated_results(self, conversation_id: str, new_result: Dict[str, Any]):
        """Remove outdated results based on the new result"""
        results = self.results_by_conversation[conversation_id]
        agent_type = new_result.get('agent_type')
        operation = new_result.get('operation')
        
        # Get the proposition or argument identifier for this result
        target_id = self._get_result_target_id(new_result)
        
        # Remove outdated results of the same type for the same target
        results[:] = [
            result for result in results
            if not self._is_outdated_result(result, agent_type, operation, target_id)
        ]
        
        # Special handling for form evaluator results
        if agent_type == 'form_evaluator':
            self._cleanup_form_evaluator_results(conversation_id, new_result)
    
    def _get_result_target_id(self, result: Dict[str, Any]) -> str:
        """Get a unique identifier for what this result targets"""
        agent_type = result.get('agent_type')
        result_content = result.get('result_content', {})
        
        if agent_type == 'builder':
            # Builder targets a specific proposition in arguments
            proposition = result_content.get('proposition', '')
            location = result_content.get('location', '')
            return f"builder:{location}:{proposition}"
        
        elif agent_type == 'formalizer':
            # Formalizer targets a specific proposition in arguments or assumptions
            proposition = result_content.get('proposition', '')
            return f"formalizer:{proposition}"
        
        elif agent_type in ['content_evaluator', 'form_evaluator']:
            # Evaluators target the entire argument as a whole
            location = result_content.get('location', '')
            return f"{agent_type}:{location}"
        
        elif agent_type == 'rewriter':
            # Rewriter targets a specific proposition
            proposition = result_content.get('proposition', '')
            return f"rewriter:{proposition}"
        
        # Fallback to using the entire result as identifier
        return f"{agent_type}:{hash(str(result))}"
    
    def _is_outdated_result(self, result: Dict[str, Any], new_agent_type: str, 
                           new_operation: str, target_id: str) -> bool:
        """Check if a result is outdated compared to a new result"""
        agent_type = result.get('agent_type')
        operation = result.get('operation')
        
        # If it's the same agent type and operation, check if it targets the same thing
        if agent_type == new_agent_type and operation == new_operation:
            result_target_id = self._get_result_target_id(result)
            return result_target_id == target_id
        
        return False
    
    def _cleanup_form_evaluator_results(self, conversation_id: str, new_result: Dict[str, Any]):
        """Special cleanup for form evaluator results when formalizations change"""
        results = self.results_by_conversation[conversation_id]
        
        # Remove all form evaluator results when a new formalization is added
        # This ensures form evaluator runs again with the new formalization
        results[:] = [
            result for result in results
            if result.get('agent_type') != 'form_evaluator'
        ]
    
    def _should_add_form_evaluator_result(self, conversation_id: str, result: Dict[str, Any]) -> bool:
        """Check if a form evaluator result should be added"""
        # Get all formalizations for this conversation
        formalizations = []
        for existing_result in self.results_by_conversation.get(conversation_id, []):
            if existing_result.get('agent_type') == 'formalizer':
                formalizations.append(existing_result)
        
        # Only add form evaluator result if we have formalizations
        return len(formalizations) > 0
    
    def get_results(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all results for a conversation"""
        results = self.results_by_conversation.get(conversation_id, [])
        
        if not results:
            return []
        
        # Update conversation timestamp on activity
        self.conversation_timestamps[conversation_id] = time.time()
        
        return results
    
    def cleanup_conversation(self, conversation_id: str):
        """Clean up all results for a conversation"""
        if conversation_id in self.results_by_conversation:
            del self.results_by_conversation[conversation_id]
        if conversation_id in self.conversation_timestamps:
            del self.conversation_timestamps[conversation_id]
        logger.debug(f"Cleaned up all results for conversation {conversation_id}")
    
    def cleanup_expired_conversations(self) -> int:
        """Clean up expired conversations and return count of removed conversations"""
        current_time = time.time()
        expired_conversations = []
        
        for conversation_id, timestamp in self.conversation_timestamps.items():
            if current_time - timestamp > AGENT_RESULT_TTL_SECONDS:
                expired_conversations.append(conversation_id)
        
        # Remove expired conversations
        for conversation_id in expired_conversations:
            del self.results_by_conversation[conversation_id]
            del self.conversation_timestamps[conversation_id]
        
        if expired_conversations:
            logger.info(f"Cleaned up {len(expired_conversations)} expired conversations")
        
        return len(expired_conversations)


class AgentCoordinator:
    """Manages background agent tasks using threading"""
    
    def __init__(self):
        self.task_queue = Queue()
        self.workers = []
        self.running = True
        self.result_manager = AgentResultManager()  # Use the new result manager
        self.task_history = {}   # Store task history by task_id
        
        # Create agents with coordinator dependency injected
        self.agents = {
            'builder': ArgumentBuilderAgent(self),
            'content_evaluator': ContentEvaluationAgent(self),
            'form_evaluator': FormEvaluationAgent(self),
            'formalizer': FormalizationAgent(self),
            'rewriter': RewriterAgent(self)
        }
        
        # Start background workers
        self._start_workers()
        logger.info("AgentCoordinator initialized with background workers")
    
    def _start_workers(self):
        """Start background worker threads for each agent type"""
        agent_types = ['builder', 'content_evaluator', 'form_evaluator', 'formalizer', 'rewriter']
        
        for agent_type in agent_types:
            worker = threading.Thread(
                target=self._worker_loop, 
                args=(agent_type,),
                name=f"agent_worker_{agent_type}"
            )
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            # logger.info(f"Started worker thread for {agent_type} agent")
    
    def _worker_loop(self, agent_type: str):
        """Main worker loop for processing tasks"""
        # logger.info(f"Worker {agent_type} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)
                
                # Check if this task is for our agent type
                if task.agent_type == agent_type:
                    # logger.info(f"Worker {agent_type} processing task {task.id}")
                    self._process_task(task)
                else:
                    # Put back in queue for different agent
                    self.task_queue.put(task)
                    
            except Exception as e:
                # Queue timeout or other error, continue
                continue
        
        # logger.info(f"Worker {agent_type} stopped")
    
    def _process_task(self, task: AgentTask):
        """Process a single task"""
        try:
            task.status = 'running'
            task.completed_at = None
            self._update_task(task)
            
            # Get the appropriate agent
            agent = self.agents.get(task.agent_type)
            if not agent:
                raise ValueError(f"Unknown agent type: {task.agent_type}")
            
            # Process the task based on agent type
            # Add conversation_id to the data for agents that need it
            task_data = {**task.data, 'conversation_id': task.conversation_id}
            
            if task.agent_type == 'builder':
                result = agent.build_argument(task_data)
            elif task.agent_type == 'content_evaluator':
                result = agent.evaluate_propositions(task_data)
            elif task.agent_type == 'form_evaluator':
                result = agent.evaluate_propositions(task_data)
            elif task.agent_type == 'formalizer':
                result = agent.formalize_proposition(task_data)
            elif task.agent_type == 'rewriter':
                result = agent.rewrite_proposition(task_data)
            else:
                raise ValueError(f"Unknown agent type: {task.agent_type}")
            
            # Convert agent result to task result
            task.result = {
                'agent_type': result.agent_type,
                'operation': result.operation,
                'result_content': result.result_content,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'target_metadata': result.target_metadata,
                'processed_at': time.time()
            }
            
            # Store result using the disciplined result manager
            self.result_manager.add_result(task.conversation_id, task.result)
                        
            # If this was a formalizer task, trigger argument state change reaction
            if task.agent_type == 'formalizer':
                # Get the argument data from the task
                argument_data = task.data.get('argument_data', {})
                if argument_data:
                    # Trigger reactive agent queueing based on the new formalization
                    self.queue_formal_evaluator_if_ready(task.conversation_id, argument_data, task.data)

            # Debug logging
            # logger.info(f"Stored result for {task.agent_type} agent in conversation {task.conversation_id}")
            # logger.debug(f"Current results for conversation {task.conversation_id}: {self.result_manager.get_results(task.conversation_id)}")
            
            task.status = 'completed'
            task.completed_at = time.time()
            
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
            task.completed_at = time.time()
            logger.error(f"Task {task.id} failed: {e}")
        
        finally:
            self._update_task(task)
    
    def _update_task(self, task: AgentTask):
        """Update task in history"""
        self.task_history[task.id] = task
    
    def queue_task(self, agent_type: str, conversation_id: str, 
                   data: Dict[str, Any], priority: int = 0) -> str:
        """Queue a new task for processing"""
        task_id = str(uuid.uuid4())
        
        task = AgentTask(
            id=task_id,
            agent_type=agent_type,
            conversation_id=conversation_id,
            data=data,
            priority=priority
        )
        
        self.task_queue.put(task)
        self.task_history[task_id] = task
        
        # logger.info(f"Queued task {task_id} for {agent_type} agent in conversation {conversation_id}")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        """Get the status of a specific task"""
        return self.task_history.get(task_id)
    
    def get_conversation_results(self, conversation_id: str) -> list:
        """Get all results for a conversation"""
        results = self.result_manager.get_results(conversation_id)
        # logger.debug(f"Retrieved {len(results)} results for conversation {conversation_id}")
        # logger.debug(f"Results: {results}")
        return results
    
    def are_conversation_tasks_complete(self, conversation_id: str) -> bool:
        """Check if all tasks for a conversation are complete"""
        # Get all tasks for this conversation from history
        conversation_tasks = [
            task for task in self.task_history.values() 
            if task.conversation_id == conversation_id
        ]
        
        if not conversation_tasks:
            return True  # No tasks means complete
        
        # Check if all tasks are completed or failed
        return all(task.status in ['completed', 'failed'] for task in conversation_tasks)
    
    def get_active_tasks(self) -> list:
        """Get all active tasks"""
        return [task for task in self.task_history.values() 
                if task.status in ['pending', 'running']]
    
    def react_to_user_argument_change(self, conversation_id: str, argument_data: Dict[str, Any], change_data: Dict[str, Any] = None):
        """
        Reactively queue agents based on user-initiated argument changes.
        This method analyzes the current argument state and queues necessary agents
        to keep results in sync with the new argument state after user modifications.
        """

        change_data = change_data or {}
        
        # Extract all propositions from the argument
        all_propositions = []
        argument_propositions = [step['proposition'] for step in argument_data.get('argument', [])]
        assumption_propositions = [step['proposition'] for step in argument_data.get('assumptions', [])]
        
        all_propositions.extend(argument_propositions)
        all_propositions.extend(assumption_propositions)
        
        # Get existing results to understand current state
        existing_results = self.get_conversation_results(conversation_id)
        
        # Queue builder agent for content discovery
        discovery_task_data = {
            'argument_data': {
                'argument': argument_data.get('argument', []),
                'assumptions': argument_data.get('assumptions', [])
            },
            **change_data
        }
        self.queue_task(
            agent_type='builder',
            conversation_id=conversation_id,
            data=discovery_task_data
        )
        
        # Queue formalizer for any new propositions
        existing_formalizations = set()
        for result in existing_results:
            if result.get('agent_type') == 'formalizer':
                existing_proposition = result.get('result_content', {}).get('proposition')
                if existing_proposition:
                    existing_formalizations.add(existing_proposition)
        
        # Queue formalizer for propositions that haven't been formalized yet
        # logger.debug(f"Queueing formalizer tasks for proposition {all_propositions}")
        for proposition in all_propositions:
            if proposition not in existing_formalizations:
                formalizer_task_data = {
                    'proposition': proposition,
                    'argument_data': discovery_task_data['argument_data'],
                    'file_ids': argument_data.get('file_ids', [])
                }
                # logger.debug(f"Queueing formalizer task for proposition {proposition}")
                self.queue_task(
                    agent_type='formalizer',
                    conversation_id=conversation_id,
                    data=formalizer_task_data
                )
        
        # Queue content evaluator for argument analysis
        analysis_task_data = {
            'argument': argument_propositions,
            'assumptions': argument_data.get('assumptions', []),
            'file_ids': argument_data.get('file_ids', []),
            'conversation_id': conversation_id
        }
        self.queue_task(
            agent_type='content_evaluator',
            conversation_id=conversation_id,
            data=analysis_task_data
        )
        
        # logger.info(f"Reactively queued agents for argument state change in conversation {conversation_id}")
    
    def queue_formal_evaluator_if_ready(self, conversation_id: str, argument_data: Dict[str, Any], change_data: Dict[str, Any] = None):
        """
        Queue a formal_evaluator task if all formalizations are in place and existing formal_evaluator is outdated.
        Checks that no formal_evaluator is already 'pending' or 'running'.
        """
        change_data = change_data or {}
        
        # logger.debug(f"Queueing formal evaluator if ready for conversation {conversation_id}")

        # Check if there's already a pending or running formal_evaluator task
        active_tasks = self.get_active_tasks()
        for task in active_tasks:
            if task.agent_type == 'form_evaluator' and task.conversation_id == conversation_id:
                logger.info(f"Form evaluator task already active for conversation {conversation_id}")
                return
        
        # logger.debug(f"Checking if formal evaluator is ready for conversation {conversation_id}")
        try:
            # Extract proposition texts from the argument for form evaluator check
            form_eval_argument_propositions = []
            
            # Extract propositions from list[Step] format
            argument_steps = argument_data.get('argument', [])
            if not isinstance(argument_steps, list):
                raise ValueError(f"Expected argument to be list[Step], got {type(argument_steps)}")
            
            for step in argument_steps:
                if not isinstance(step, dict):
                    raise ValueError(f"Expected step to be dict, got {type(step)}")
                proposition = step.get('proposition', '')
                if proposition:
                    form_eval_argument_propositions.append(proposition)

            # logger.debug(f"Form evaluator argument propositions: {form_eval_argument_propositions}")

            # Get existing formalizations
            existing_results = self.get_conversation_results(conversation_id)

            # logger.debug(f"Existing results: {existing_results}")

            formalized_propositions = set()
            for result in existing_results:
                if result.get('agent_type') == 'formalizer':
                    existing_proposition = result.get('result_content', {}).get('proposition')
                    if existing_proposition:
                        formalized_propositions.add(existing_proposition)
            
            # Check if all propositions are now formalized
            form_eval_argument_propositions_set = set(form_eval_argument_propositions)

            # logger.debug(f"Formalized propositions: {formalized_propositions}")
            
            if form_eval_argument_propositions_set.issubset(formalized_propositions):
                # Queue form evaluator task
                form_evaluator_task_data = {
                    'argument': form_eval_argument_propositions,
                    'assumptions': argument_data.get('assumptions', []),
                    'file_ids': argument_data.get('file_ids', []),
                    **change_data
                }
                
                self.queue_task(
                    agent_type='form_evaluator',
                    conversation_id=conversation_id,
                    data=form_evaluator_task_data
                )
                # logger.info(f"Queued form evaluator task for conversation {conversation_id}")
            else:
                pass
                # logger.info(f"Not all propositions formalized yet for conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error checking and queueing form evaluator: {e}")
    
    def stop(self):
        """Stop all workers"""
        self.running = False
        logger.info("AgentCoordinator stopping all workers")
    

# Global coordinator instance
coordinator = AgentCoordinator() 
