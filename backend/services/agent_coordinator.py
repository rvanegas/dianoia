import threading
import time
import uuid
from queue import Queue
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from core.utils import logger
from services.agents import AGENTS


@dataclass
class AgentTask:
    """Represents a task for an agent to process"""
    id: str
    agent_type: str  # 'builder', 'evaluator', 'formalizer', 'rewriter'
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


class AgentCoordinator:
    """Manages background agent tasks using threading"""
    
    def __init__(self):
        self.task_queue = Queue()
        self.workers = []
        self.running = True
        self.agent_results = {}  # Store results by conversation_id
        self.task_history = {}   # Store task history by task_id
        
        # Start background workers
        self._start_workers()
        logger.info("AgentCoordinator initialized with background workers")
    
    def _start_workers(self):
        """Start background worker threads for each agent type"""
        agent_types = ['builder', 'evaluator', 'formalizer', 'rewriter']
        
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
            agent = AGENTS.get(task.agent_type)
            if not agent:
                raise ValueError(f"Unknown agent type: {task.agent_type}")
            
            # Process the task based on agent type
            if task.agent_type == 'builder':
                result = agent.build_argument(task.data)
            elif task.agent_type == 'evaluator':
                result = agent.evaluate_propositions(task.data)
            elif task.agent_type == 'formalizer':
                result = agent.formalize_proposition(task.data)
            elif task.agent_type == 'rewriter':
                result = agent.rewrite_proposition(task.data)
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
            
            # Store result by conversation_id
            if task.conversation_id not in self.agent_results:
                self.agent_results[task.conversation_id] = []
            self.agent_results[task.conversation_id].append(task.result)
            
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
        
        logger.info(f"Queued task {task_id} for {agent_type} agent")
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        """Get the status of a specific task"""
        return self.task_history.get(task_id)
    
    def get_conversation_results(self, conversation_id: str) -> list:
        """Get all results for a conversation"""
        results = self.agent_results.get(conversation_id, [])
        return results
    
    def are_conversation_tasks_complete(self, conversation_id: str) -> bool:
        """Check if all tasks for a conversation are complete"""
        # Get all tasks for this conversation
        conversation_tasks = [
            task for task in self.task_history.values() 
            if task.conversation_id == conversation_id
        ]
        
        if not conversation_tasks:
            return True  # No tasks means complete
        
        # Check if all tasks are completed or failed
        all_complete = all(
            task.status in ['completed', 'failed'] 
            for task in conversation_tasks
        )
        
        return all_complete
    
    def get_active_tasks(self) -> list:
        """Get all active tasks"""
        return [task for task in self.task_history.values() 
                if task.status in ['pending', 'running']]
    
    def stop(self):
        """Stop all workers"""
        self.running = False
        logger.info("AgentCoordinator stopping all workers")


# Global coordinator instance
coordinator = AgentCoordinator() 
