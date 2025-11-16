import threading
import time
import uuid
from queue import Queue
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from core.utils import logger
from services.agents import ArgumentBuilderAgent, ContentEvaluationAgent, FormEvaluationAgent, FormalizationAgent, RewriterAgent


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
    """Manages agent results with disciplined cleanup and maintenance"""
    
    def __init__(self):
        self.results_by_conversation: Dict[str, List[Dict[str, Any]]] = {}
    
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
        
        # Add the new result
        self.results_by_conversation[conversation_id].append(result)
    
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
        data = result.get('data', {})
        
        if agent_type == 'builder':
            # Builder targets a specific proposition in arguments
            proposition = data.get('proposition', '')
            location = data.get('location', '')
            return f"builder:{location}:{proposition}"
        
        elif agent_type == 'formalizer':
            # Formalizer targets a specific proposition in arguments or assumptions
            proposition = data.get('proposition', '')
            return f"formalizer:{proposition}"
        
        elif agent_type in ['content_evaluator', 'form_evaluator']:
            # Evaluators target the entire argument as a whole
            location = data.get('location', '')
            return f"{agent_type}:{location}"
        
        elif agent_type == 'rewriter':
            # Rewriter targets a specific proposition
            proposition = data.get('proposition', '')
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
        return self.results_by_conversation.get(conversation_id, [])
    
    def cleanup_conversation(self, conversation_id: str):
        """Clean up all results for a conversation"""
        if conversation_id in self.results_by_conversation:
            del self.results_by_conversation[conversation_id]


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
            logger.info(f"Started worker thread for {agent_type} agent")
    
    def _worker_loop(self, agent_type: str):
        """Main worker loop for processing tasks"""
        logger.info(f"Worker {agent_type} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)
                
                # Check if this task is for our agent type
                if task.agent_type == agent_type:
                    logger.info(f"Worker {agent_type} processing task {task.id}")
                    self._process_task(task)
                else:
                    # Put back in queue for different agent
                    self.task_queue.put(task)
                    
            except Exception as e:
                # Queue timeout or other error, continue
                continue
        
        logger.info(f"Worker {agent_type} stopped")
    
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
                'data': result.data,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'processed_at': time.time()
            }
            
            # Store result using the disciplined result manager
            self.result_manager.add_result(task.conversation_id, task.result)
            
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
    
    def cleanup_conversation_results(self, conversation_id: str):
        """Clean up all results for a conversation"""
        self.result_manager.cleanup_conversation(conversation_id)
        logger.info(f"Cleaned up results for conversation {conversation_id}")
    
    def check_formalization_completion(self, conversation_id: str, argument: list) -> bool:
        """Check if all propositions in an argument have been formalized"""
        try:
            # Get existing results for this conversation
            existing_results = self.get_conversation_results(conversation_id)
            
            # Get formalized propositions
            formalized_propositions = set()
            for result in existing_results:
                if result.get('agent_type') == 'formalizer':
                    existing_proposition = result.get('data', {}).get('proposition')
                    if existing_proposition:
                        formalized_propositions.add(existing_proposition)
            
            # Check if all argument propositions have been formalized
            argument_propositions = set(argument)
            return argument_propositions.issubset(formalized_propositions)
            
        except Exception as e:
            logger.error(f"Error checking formalization completion: {e}")
            return False
    
    def react_to_argument_state_change(self, conversation_id: str, argument_data: Dict[str, Any], change_data: Dict[str, Any] = None):
        """
        Reactively queue agents based on argument state changes.
        This method analyzes the current argument state and queues necessary agents
        to keep results in sync with the new argument state.
        """
        change_data = change_data or {}
        
        # Extract all propositions from the argument
        all_propositions = []
        argument_propositions = [step['proposition'] for step in argument_data.get('argument', [])]
        counter_argument_propositions = [step['proposition'] for step in argument_data.get('counter_argument', [])]
        assumption_propositions = [step['proposition'] for step in argument_data.get('assumptions', [])]
        
        all_propositions.extend(argument_propositions)
        all_propositions.extend(counter_argument_propositions)
        all_propositions.extend(assumption_propositions)
        
        # Get existing results to understand current state
        existing_results = self.get_conversation_results(conversation_id)
        
        # Queue builder agent for content discovery
        discovery_task_data = {
            'argument_data': {
                'argument': argument_data.get('argument', []),
                'counter_argument': argument_data.get('counter_argument', []),
                'assumptions': argument_data.get('assumptions', []),
                'thesis': argument_data.get('thesis', ''),
                'counter_thesis': argument_data.get('counter_thesis', ''),
                'presupposition': argument_data.get('presupposition', '')
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
                existing_proposition = result.get('data', {}).get('proposition')
                if existing_proposition:
                    existing_formalizations.add(existing_proposition)
        
        # Queue formalizer for propositions that haven't been formalized yet
        for proposition in all_propositions:
            if proposition not in existing_formalizations:
                formalizer_task_data = {
                    'proposition': proposition,
                    'argument_data': discovery_task_data['argument_data'],
                    'file_ids': argument_data.get('file_ids', [])
                }
                self.queue_task(
                    agent_type='formalizer',
                    conversation_id=conversation_id,
                    data=formalizer_task_data
                )
        
        # Queue content evaluator for argument analysis
        analysis_task_data = {
            'argument': argument_propositions,
            'thesis': argument_data.get('thesis', ''),
            'counter_thesis': argument_data.get('counter_thesis', ''),
            'assumptions': argument_data.get('assumptions', []),
            'file_ids': argument_data.get('file_ids', []),
            **change_data
        }
        self.queue_task(
            agent_type='content_evaluator',
            conversation_id=conversation_id,
            data=analysis_task_data
        )
        
        # Queue form evaluator if we have formalizations
        if existing_formalizations:
            form_evaluator_task_data = {
                'argument': argument_propositions,
                'thesis': argument_data.get('thesis', ''),
                'counter_thesis': argument_data.get('counter_thesis', ''),
                'assumptions': argument_data.get('assumptions', []),
                'file_ids': argument_data.get('file_ids', []),
                **change_data
            }
            self.queue_task(
                agent_type='form_evaluator',
                conversation_id=conversation_id,
                data=form_evaluator_task_data
            )
        
        logger.info(f"Reactively queued agents for argument state change in conversation {conversation_id}")
    
    def stop(self):
        """Stop all workers"""
        self.running = False
        logger.info("AgentCoordinator stopping all workers")


# Global coordinator instance
coordinator = AgentCoordinator() 
