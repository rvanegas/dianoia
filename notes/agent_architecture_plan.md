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

### 1. Agent Coordination Strategy

**Three Development Options:**

**Option 1: Backend-Driven Coordination (Current Choice)**
- Backend manages all agent coordination and task scheduling
- Agents are reactive to backend decisions
- Centralized control and deterministic behavior
- **Pros**: Easier to implement, debug, and control
- **Cons**: Less agent autonomy, backend becomes complex coordinator

**Option 2: Agent-Driven Coordination**
- Agents make autonomous decisions about what to work on
- Agents communicate directly with each other
- Backend provides limits, monitoring, and user interface
- **Pros**: True agent autonomy, flexible coordination
- **Cons**: Harder to debug, potential race conditions, complex state management

**Option 3: Hybrid Approach**
- Backend manages high-level coordination
- Agents have domain-specific autonomy
- Shared context with agent communication
- **Pros**: Best of both worlds, progressive enhancement
- **Cons**: Most complex to design and implement

**Current Implementation**: We are beginning with **Option 1 (Backend-Driven)** to establish a solid foundation, while leaving open the possibility of advancing to Options 2 or 3 as the system matures and requirements become clearer.

### 2. Background Agent System

**Agent Types:**
- **Argument Builder Agent**: Continuously generates complex multi-step arguments *(Primary Focus)*
- **Evaluation Agent**: Continuously assesses truth/validity of all propositions *(Stub)*
- **Formalization Agent**: Suggests formalizations and alternative phrasings *(Stub)*
- **Rewriter Agent**: Recommends proposition rewrites, rephrasing, and splitting *(Stub)*

**Development Strategy**: Build complete end-to-end loop with Builder Agent first, then incrementally add other agents as fully functional components.

### 2. Continuous Background Agent Iteration

**Vision**: Agents continuously examine every proposition and try to improve them in various ways (formalization, rewriting, justifying, evaluating). User interactions consist of selecting from among the various options generated in the background.

**Key Principles**:
- **Natural Language is Canonical**: Only natural language propositions are the source of truth
- **Formalizations are Optional**: Agents can work with or without formalization guidance
- **Multiple Formalizations**: Zero, one, or more formalizations per proposition
- **User Endorsement Matters**: Endorsed formalizations influence agent interpretations
- **Bidirectional Inspiration**: Justifications can inspire formalizations and vice versa
- **No Final Formalizations**: All formalizations are tentative until user endorsed

```python
class AgentCoordinator:
    def __init__(self):
        self.task_queue = Queue()
        self.workers = []
        self.running = True
        self.agent_results = {}  # Store results by conversation_id
        self.iteration_limits = IterationLimits()
        self.conversation_states = {}  # Track what agents have tried
        
    def start_workers(self):
        # Start background worker threads for each agent type
        for agent_type in ['builder', 'evaluator', 'formalizer', 'rewriter']:
            worker = threading.Thread(target=self._worker_loop, args=(agent_type,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self, agent_type: str):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task.agent_type == agent_type:
                    self._process_task(task)
                else:
                    # Put back in queue for different agent
                    self.task_queue.put(task)
            except:
                continue
    
    def iterate_on_conversation(self, conversation_id: str):
        """Each agent continuously improves every proposition with optional guidance"""
        conv_state = self.conversation_states.get(conversation_id, {})
        context = self.get_conversation_context(conversation_id)
        
        # Builder Agent: Justify with optional formalization guidance
        for prop in self._get_all_propositions(conversation_id):
            if self._should_justify_proposition(prop, conv_state):
                self.queue_task('builder', 'justify_proposition', conversation_id, {
                    'proposition': prop,
                    'target_loc': prop.location,
                    'target_index': prop.index,
                    'available_formalizations': context.get_formalizations(prop.id),
                    'user_endorsed_formalization': context.get_endorsed_formalization(prop.id)
                })
        
        # Evaluator Agent: Evaluate with optional formalization guidance
        for arg in self._get_all_arguments(conversation_id):
            if self._should_evaluate_argument(arg, conv_state):
                self.queue_task('evaluator', 'evaluate_argument', conversation_id, {
                    'argument': arg,
                    'assumptions': self._get_assumptions(conversation_id),
                    'available_formalizations': context.get_formalizations_for_argument(arg),
                    'user_endorsed_formalizations': context.get_endorsed_formalizations_for_argument(arg)
                })
        
        # Formalizer Agent: Formalize with optional justification inspiration
        for prop in self._get_all_propositions(conversation_id):
            if self._should_formalize_proposition(prop, conv_state):
                self.queue_task('formalizer', 'formalize_proposition', conversation_id, {
                    'proposition': prop.text,
                    'available_justifications': context.get_justifications(prop.id),
                    'available_evaluations': context.get_evaluations(prop.id)
                })
        
        # Rewriter Agent: Rewrite with optional formalization guidance
        for prop in self._get_all_propositions(conversation_id):
            if self._should_rewrite_proposition(prop, conv_state):
                self.queue_task('rewriter', 'rewrite_proposition', conversation_id, {
                    'proposition': prop.text,
                    'context': self._get_proposition_context(conversation_id, prop),
                    'available_formalizations': context.get_formalizations(prop.id),
                    'user_endorsed_formalization': context.get_endorsed_formalization(prop.id)
                })

class IterationLimits:
    """Hard limits to prevent runaway iteration"""
    MAX_JUSTIFICATIONS_PER_PROPOSITION = 3
    MAX_EVALUATIONS_PER_ARGUMENT = 2
    MAX_FORMALIZATIONS_PER_PROPOSITION = 5
    MAX_REWRITES_PER_PROPOSITION = 4
    MAX_ITERATIONS_PER_CONVERSATION = 100
    COOLDOWN_PERIOD = 30  # seconds between iterations
    MAX_CONCURRENT_TASKS_PER_CONVERSATION = 5

class SharedContext:
    """Shared context for agent coordination and user endorsements"""
    def __init__(self):
        self.formalizations = {}  # proposition_id -> List[Formalization]
        self.justifications = {}  # proposition_id -> List[Justification]
        self.evaluations = {}     # proposition_id -> List[Evaluation]
        self.rewrites = {}        # proposition_id -> List[Rewrite]
        self.user_endorsements = {}  # proposition_id -> endorsed_formalization_id
        self.shared_predicates = {}
        self.shared_constants = {}
    
    def add_formalization(self, proposition_id: str, formalization: Formalization):
        """Add formalization without removing others"""
        if proposition_id not in self.formalizations:
            self.formalizations[proposition_id] = []
        self.formalizations[proposition_id].append(formalization)
    
    def get_formalizations(self, proposition_id: str) -> List[Formalization]:
        """Get all formalizations for a proposition"""
        return self.formalizations.get(proposition_id, [])
    
    def get_endorsed_formalization(self, proposition_id: str) -> Optional[str]:
        """Get user-endorsed formalization ID if any"""
        return self.user_endorsements.get(proposition_id)
    
    def endorse_formalization(self, proposition_id: str, formalization_id: str):
        """User endorses a specific formalization"""
        self.user_endorsements[proposition_id] = formalization_id
```

### 3. Browser-Based State Management

**Key Constraint**: All state remains in the browser, no database persistence for agent tasks or suggestions.

```typescript
// Frontend state extensions
interface AgentTask {
    id: string;
    agent_type: 'builder' | 'evaluator' | 'formalizer' | 'rewriter';
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
        loc: string;  // 'argument' | 'assumptions'
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

### 4. Agent Decision Logic and Continuous Improvement

#### **Agent Decision Making**
```python
class AgentDecisionLogic:
    def should_justify_proposition(self, proposition, conv_state):
        """Builder agent decides if proposition needs justification"""
        return (
            not proposition.has_justification() and
            proposition.justification_count < self.limits.MAX_JUSTIFICATIONS_PER_PROPOSITION and
            not self._recently_worked_on(proposition, conv_state) and
            self._has_work_capacity(conv_state)
        )
    
    def should_evaluate_argument(self, argument, conv_state):
        """Evaluator agent decides if argument needs evaluation"""
        return (
            argument.has_justifiers() and
            argument.evaluation_count < self.limits.MAX_EVALUATIONS_PER_ARGUMENT and
            not self._recently_evaluated(argument, conv_state)
        )
    
    def should_formalize_proposition(self, proposition, conv_state):
        """Formalizer agent decides if proposition needs formalization"""
        return (
            not proposition.has_formalization() and
            proposition.formalization_count < self.limits.MAX_FORMALIZATIONS_PER_PROPOSITION and
            not self._recently_formalized(proposition, conv_state)
        )
    
    def should_rewrite_proposition(self, proposition, conv_state):
        """Rewriter agent decides if proposition needs rewriting"""
        return (
            not proposition.has_rewrite() and
            proposition.rewrite_count < self.limits.MAX_REWRITES_PER_PROPOSITION and
            not self._recently_rewritten(proposition, conv_state)
        )
```

#### **Continuous Background Iteration**
- **Builder Agent**: Justifies propositions with optional formalization guidance
- **Evaluator Agent**: Evaluates arguments with optional formalization guidance
- **Formalizer Agent**: Formalizes propositions with optional justification inspiration
- **Rewriter Agent**: Rewrites propositions with optional formalization guidance
- **User Endorsements**: Endorsed formalizations influence agent interpretations
- **Cooldown Periods**: Prevent agents from working on same item repeatedly
- **Hard Limits**: Prevent runaway iteration and resource exhaustion

### 5. User Experience: Selection-Based Interaction

#### **Background Agent Work**
- Agents work continuously in background
- No user waiting or blocking
- Multiple options generated for each proposition
- User sees suggestions as they become available

#### **User Selection Interface**
```typescript
interface PropositionOptions {
    proposition_id: string;
    original_text: string;
    justifications: Array<{
        id: string;
        text: string;
        confidence: number;
        agent_reasoning: string;
        used_formalization?: string;  // If formalization was used as guidance
    }>;
    formalizations: Array<{
        id: string;
        formula: string;
        unicode: string;
        confidence: number;
        reasoning: string;
        is_endorsed: boolean;
        inspired_by_justification?: string;  // If justification inspired this formalization
    }>;
    rewrites: Array<{
        id: string;
        original_text: string;
        rewritten_text: string;
        rewrite_type: 'rephrase' | 'split' | 'clarify';
        confidence: number;
        reasoning: string;
        used_formalization?: string;  // If formalization was used as guidance
    }>;
    evaluations: Array<{
        truth_score: number;
        validity_score: number;
        confidence: number;
        used_formalization?: string;  // If formalization was used in evaluation
    }>;
}

interface UserEndorsement {
    proposition_id: string;
    formalization_id: string;
    endorsed_at: number;
}
```

#### **User Workflow**
1. **Create conversation** → Agents start working immediately
2. **See suggestions** → Multiple options appear for each proposition
3. **Endorse formalizations** → User can endorse specific formalizations
4. **Select preferences** → Choose best justifications, rewrites, etc.
5. **Conversation updates** → Selected options become part of argument
6. **Continuous improvement** → Agents continue working with endorsed formalizations as guidance

### 6. Agent Implementation Strategy

#### **Argument Builder Agent**
- **Continuous Trigger**: Justifies propositions with optional formalization guidance
- **Capabilities**:
  - Generate justifications without formalization guidance (generative)
  - Generate justifications with formalization guidance when available
  - Generate multi-step argument chains (not just 1-2 propositions)
  - Identify logical gaps and suggest bridging propositions
  - Create alternative argument paths
  - Suggest counter-arguments to existing steps
- **Output**: Multiple justification options with formalization usage tracking
- **Interdependencies**: Can work with or without formalization guidance

#### **Evaluation Agent**
- **Continuous Trigger**: Evaluates arguments with optional formalization guidance
- **Capabilities**:
  - Evaluate without formalization guidance
  - Evaluate with formalization guidance when available
  - Continuous truth/validity assessment
  - Confidence scoring
  - Identify weak links in arguments
  - Suggest strengthening propositions
- **Output**: Evaluation scores with formalization usage tracking
- **Interdependencies**: Can work with or without formalization guidance

#### **Formalization Agent**
- **Continuous Trigger**: Suggests formalizations and rewrites for all propositions
- **Capabilities**:
  - Suggest formal logical representations using `core/logic.py` constraints
  - Rephrase propositions for clarity and precision
  - Split complex propositions into simpler components
  - Clarify ambiguous or vague language
  - Identify implicit assumptions through formal analysis
  - Suggest alternative formulations that maintain logical content
  - Provide multiple formalization and rewrite options for user selection
  - Coordinate formalization choices with natural language rewrites
- **Output**: Multiple formalization options with corresponding natural language rewrites
- **Tools**: Access to `core/logic.py` formalization functions as agent tools
- **Interdependencies**: Formalization choices inform rewrite suggestions and vice versa

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

#### **Phase 1: Builder Agent Focus (Week 1)**
- [x] Implement threading-based task queue system
- [x] Create agent coordination framework
- [x] Extend data models for agent tasks
- [x] Add basic agent result storage
- [x] Implement real agent logic with LLM integration
- [ ] Implement full builder agent with LLM integration
- [ ] Add shared context (justifications only for now)
- [ ] Add user endorsement system (for future formalizations)
- [ ] Create stub agents (evaluator, formalizer, rewriter)
- [ ] Build frontend for builder suggestions

#### **Phase 2: Shared Context & Coordination (Week 2)**
- [ ] Add shared context management system
- [ ] Implement user endorsement tracking
- [ ] Add optional formalization guidance for agents
- [ ] Add iteration limits and tracking system
- [ ] Implement agent decision logic
- [ ] Add conversation state tracking
- [ ] Implement cooldown periods
- [ ] Add hard limits per proposition/argument

#### **Phase 3: Agent Communication & Dependencies (Week 3)**
- [ ] Implement agent-to-agent communication protocols
- [ ] Add dependency-based task queuing
- [ ] Implement result broadcasting system
- [ ] Add conversation state management
- [ ] Implement continuous background iteration
- [ ] Add agent scanning for work opportunities
- [ ] Implement automatic task queuing

#### **Phase 4: User Interface & Selection (Week 4)**
- [ ] Implement user endorsement interface
- [ ] Add formalization selection workflow
- [ ] Implement inspiration tracking display
- [ ] Add multiple options display for each proposition
- [ ] Implement user selection workflow
- [ ] Add conversation update based on selections
- [ ] Implement real-time suggestion updates

#### **Phase 5: Advanced Features & Optimization (Week 5-6)**
- [ ] Integrate `core/logic.py` formalization constraints
- [ ] Add sophisticated agent reasoning with formal logic awareness
- [ ] Implement agent learning from user feedback
- [ ] Add performance optimization
- [ ] Implement advanced coordination strategies
- [ ] Add shared context management optimization

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