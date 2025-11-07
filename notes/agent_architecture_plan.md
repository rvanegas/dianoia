# Dianoia Multi-Agent Architecture Implementation Plan

## Overview
Transform dianoia from a reactive system into a proactive, intelligent argumentation assistant with background agents that continuously work to improve arguments.

## Current Architecture Analysis

**Existing System:**
- **AI Justify**: Generates 1-2 propositions to support a conclusion
- **Evaluate**: Assesses truth/validity scores for argument steps
- **Basic argument structure**: Thesis, counter-thesis, assumptions, and argument steps
- **Synchronous user-driven workflow**: User triggers operations, waits for results

## Proposed Multi-Agent Architecture

### 1. Background Agent System

**Agent Types:**
- **Argument Builder Agent**: Continuously generates complex multi-step arguments
- **Evaluation Agent**: Continuously assesses truth/validity of all propositions
- **Formalization Agent**: Suggests formalizations and alternative phrasings

### 2. Threading-Based Agent Coordination

```python
class AgentCoordinator:
    def __init__(self):
        self.task_queue = Queue()
        self.workers = []
        self.running = True
        self.agent_results = {}  # Store results by conversation_id
        
    def start_workers(self):
        # Start background worker threads for each agent type
        for agent_type in ['builder', 'evaluator', 'formalizer']:
            worker = threading.Thread(target=self._worker_loop, args=(agent_type,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self, agent_type):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task['agent_type'] == agent_type:
                    result = self._process_task(task)
                    self._store_result(task['conversation_id'], result)
                else:
                    # Put back in queue for different agent
                    self.task_queue.put(task)
            except:
                continue
```

### 3. Browser-Based State Management

**Key Constraint**: All state remains in the browser, no database persistence for agent tasks or suggestions.

```typescript
// Frontend state extensions
interface AgentTask {
    id: string;
    task_type: 'build_argument' | 'evaluate' | 'formalize';
    agent_type: 'builder' | 'evaluator' | 'formalizer';
    status: 'pending' | 'running' | 'completed' | 'failed';
    priority: number;
    created_at: number;
    completed_at?: number;
    result?: any;
}

interface AgentSuggestion {
    id: string;
    proposition: string;
    placement: {
        loc: string;  // 'argument' | 'counter_argument' | 'assumptions'
        index: number;
    };
    confidence: number;
    agent_type: string;
    reasoning: string;
    created_at: number;
    approved?: boolean;
    rejected?: boolean;
}

interface FormalizationRecommendation {
    id: string;
    original_proposition: string;
    formalizations: Array<{
        formula: string;  // ASCII representation from core/logic.py
        unicode: string;  // Unicode representation
        reasoning: string;
        confidence: number;
    }>;
    agent_type: string;
    created_at: number;
    user_selection?: number;  // index of selected formalization
}

// Extend existing ConversationSnapshot
interface ConversationSnapshot {
    // ... existing fields ...
    agent_tasks: AgentTask[];
    agent_suggestions: AgentSuggestion[];
    formalization_recommendations: FormalizationRecommendation[];
    agent_status: {
        builder_active: boolean;
        evaluator_active: boolean;
        formalizer_active: boolean;
    };
}
```

### 4. Agent Implementation Strategy

#### **Argument Builder Agent**
- **Trigger**: New thesis/counter-thesis creation, or periodic background analysis
- **Capabilities**:
  - Generate multi-step argument chains (not just 1-2 propositions)
  - Identify logical gaps and suggest bridging propositions
  - Create alternative argument paths
  - Suggest counter-arguments to existing steps
- **Output**: New propositions with suggested placements in argument structure

#### **Evaluation Agent**
- **Trigger**: New propositions added, or periodic re-evaluation
- **Capabilities**:
  - Continuous truth/validity assessment
  - Confidence scoring
  - Identify weak links in arguments
  - Suggest strengthening propositions
- **Output**: Updated evaluation scores and recommendations

#### **Formalization Agent**
- **Trigger**: New propositions, user requests, or background analysis
- **Capabilities**:
  - Suggest formal logical representations using `core/logic.py` constraints
  - Recommend alternative phrasings based on formalization choices
  - Identify implicit assumptions through formal analysis
  - Suggest clearer formulations that align with formal logic
  - Provide multiple formalization options for user selection
  - Rewrite natural language based on user's formalization choice
- **Output**: Multiple formalization options with reasoning, plus natural language rewrites
- **Tools**: Access to `core/logic.py` formalization functions as agent tools

### 5. Threading-Based Background Processing

```python
class BackgroundTaskManager:
    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.coordinator.start_workers()
    
    def queue_agent_task(self, agent_type, conversation_id, data):
        task = {
            'agent_type': agent_type,
            'conversation_id': conversation_id,
            'data': data,
            'timestamp': time.time(),
            'status': 'pending'
        }
        self.coordinator.task_queue.put(task)
    
    def get_agent_results(self, conversation_id):
        return self.coordinator.agent_results.get(conversation_id, [])
```

### 6. User Interface Enhancements

- **Real-time updates**: WebSocket connections for live agent activity
- **Suggestion panel**: Display agent recommendations for user approval
- **Agent status indicators**: Show which agents are working on what
- **Conflict resolution UI**: Handle when agents suggest conflicting propositions

### 7. Implementation Phases

#### **Phase 1: Foundation (Week 1)**
- [ ] Implement threading-based task queue system
- [ ] Create agent coordination framework
- [ ] Extend data models for agent tasks
- [ ] Add basic agent result storage

#### **Phase 2: Core Agents (Week 2-3)**
- [ ] Implement Argument Builder Agent
- [ ] Implement Evaluation Agent
- [ ] Basic agent communication
- [ ] Agent result persistence

#### **Phase 3: Advanced Features (Week 4-5)**
- [ ] Implement Formalization Agent with `core/logic.py` integration
- [ ] Add sophisticated agent reasoning with formal logic awareness
- [ ] Implement user approval workflow for suggestions
- [ ] Add formalization recommendation system with multiple options
- [ ] Implement natural language rewrite based on formalization choices
- [ ] Add agent learning from user feedback

#### **Phase 4: Optimization (Week 6)**
- [ ] Performance optimization
- [ ] Advanced coordination strategies
- [ ] Agent performance metrics
- [ ] Error handling and recovery
- [ ] Formal logic inference pattern recognition
- [ ] Advanced formalization constraint validation

### 8. Technical Implementation

#### **Dependencies to Add:**
```python
# requirements.txt additions
websockets==12.0  # For real-time UI updates
```

#### **Agent Tools Integration:**

```python
# New agent tools leveraging core/logic.py
class FormalizationTools:
    """Tools for agents to use core/logic.py formalization constraints"""
    
    def formalize_proposition(self, natural_language: str) -> List[Dict]:
        """Generate multiple formalization options using core/logic.py constraints"""
        # Use existing logic.py classes and constraints
        # Return multiple valid formalization options
        
    def validate_inference(self, premises: List[str], conclusion: str) -> Dict:
        """Check if inference is valid using formal logic patterns"""
        # Validate inference patterns in formal logic
        
    def suggest_rewrites(self, formalization: str) -> List[str]:
        """Suggest natural language rewrites based on formalization choice"""
        # Generate alternative natural language formulations
        
    def check_formal_constraints(self, formula: str) -> bool:
        """Validate formula against core/logic.py constraints"""
        # Ensure formula follows Variable/Constant naming rules, etc.
```

#### **Formal Logic Integration:**
- Agents have access to `core/logic.py` classes and constraints
- Formalization follows strict naming conventions (p-z for variables, a-o for constants)
- Agents can validate inference patterns in formal logic
- Support for quantifiers, modal operators, binary operations

#### **API Endpoints:**
```python
# New endpoints
POST /api/v1/agents/trigger-builder
POST /api/v1/agents/trigger-evaluator
POST /api/v1/agents/trigger-formalizer
GET /api/v1/agents/status
GET /api/v1/agents/suggestions
POST /api/v1/agents/approve-suggestion
POST /api/v1/agents/reject-suggestion
POST /api/v1/agents/select-formalization
POST /api/v1/agents/rewrite-proposition
GET /api/v1/agents/formalization-tools
```

### 9. Agent Intelligence Features

- **Context awareness**: Agents understand full argument structure
- **Learning**: Agents improve based on user feedback
- **Collaboration**: Agents can build on each other's work
- **Conflict resolution**: Handle when agents suggest contradictory propositions
- **Formal logic awareness**: Agents understand valid inference patterns in formal logic
- **Formalization constraints**: Agents use `core/logic.py` constraints for valid formalizations
- **Multi-step reasoning**: Agents can chain formal inferences and validate them

### 10. Threading Advantages for This Use Case

- **Simplicity**: No external dependencies (Redis, Celery workers)
- **Single-server**: Perfect for current deployment
- **I/O bound tasks**: LLM calls are ideal for threading
- **Easy debugging**: All code runs in same process
- **Quick development**: Minimal setup time

### 11. Formalization Workflow

#### **Multi-Step Formalization Process:**
1. **Agent Analysis**: Formalization agent analyzes natural language proposition
2. **Multiple Options**: Agent generates 2-3 different formalization options using `core/logic.py` constraints
3. **User Selection**: User chooses the most accurate formalization from options
4. **Natural Language Rewrite**: Agent suggests rewritten natural language based on chosen formalization
5. **Validation**: System validates that formalization follows all `core/logic.py` constraints

#### **Formalization Agent Tools:**
```python
# Agent has access to these tools
- formalize_proposition(natural_language) -> List[FormalizationOption]
- validate_inference(premises, conclusion) -> ValidityResult
- suggest_rewrites(formalization) -> List[str]
- check_formal_constraints(formula) -> bool
```

#### **User Interface for Formalization:**
- **Formalization Panel**: Shows multiple formalization options with reasoning
- **Selection Interface**: User can select preferred formalization
- **Rewrite Preview**: Shows suggested natural language rewrite
- **Validation Indicators**: Visual indicators for constraint compliance

### 12. Migration Path

**Future scaling options:**
- Replace threading with Celery when multi-server deployment needed
- Add Redis for task persistence across server restarts
- Implement distributed workers for high-load scenarios

## Success Metrics

- **Agent productivity**: Number of useful suggestions generated
- **User engagement**: Frequency of agent suggestion approvals
- **Argument quality**: Improvement in evaluation scores over time
- **System performance**: Response times and resource usage

## Risk Mitigation

- **Thread safety**: Careful handling of shared data structures
- **Error isolation**: Agent failures shouldn't crash main application
- **Resource management**: Limit concurrent agent operations
- **User control**: Always allow users to disable/approve agent actions
- **Formalization constraints**: Ensure all formalizations follow `core/logic.py` rules
- **State consistency**: Browser state must remain consistent with agent operations
- **Formal logic validation**: All agent formalizations must be validated against constraints 