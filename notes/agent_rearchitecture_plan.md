# Agent Rearchitecture Plan

## Overview

This document outlines a comprehensive rearchitecture of the agent system in Dianoia, addressing six key areas:

1. **Input Normalization** - Standardize how agents receive and process input
2. **Agent Type Reorganization** - Restructure agent functions into a new array of agent types
3. **Trigger Mechanism Rearchitecture** - Redesign how agents are triggered and coordinated
4. **Snapshot Association** - Associate agents with conversation snapshots, not just conversations
5. **TTL Implementation** - Introduce time-to-live mechanisms on agent results
6. **Frontend Integration** - Propagate changes to the frontend accordingly

## Current State Analysis

### Existing Architecture
- **Agent Types**: `builder`, `content_evaluator`, `form_evaluator`, `formalizer`, `rewriter`
- **Coordination**: Backend-driven with `AgentCoordinator` managing task queues
- **Triggering**: Reactive to argument state changes via `react_to_user_argument_change()`
- **Association**: Agents tied to `conversation_id` only
- **Results**: Stored in `AgentResultManager` with basic cleanup
- **Frontend**: `AllAgentResults` component displays results by conversation

### Current Issues
1. **Input Inconsistency**: Different agents receive data in different formats
2. **Agent Overlap**: Some agents have overlapping responsibilities
3. **Rigid Triggering**: Agents only trigger on specific argument changes
4. **No Snapshot Awareness**: Agents don't understand conversation history/context
5. **No Result Expiration**: Results persist indefinitely
6. **Limited Frontend Integration**: Basic result display without rich interaction

## 1. Input Normalization

### Problem
Agents currently receive data in inconsistent formats:
- `builder` receives `argument_data` with nested structure
- `content_evaluator` receives flat `argument` and `assumptions` lists
- `formalizer` receives individual `proposition` strings
- No standardized context or metadata

### Solution: Normalized Agent Input Schema

```typescript
interface AgentInput {
  // Core identification
  conversation_id: string
  snapshot_id: string
  
  // Context data
  context: {
    assumptions: Step[]
    argument: Step[]
    file_ids: string[]
    user_preferences: UserPreferences
  }
  
  // Note: Step model must be updated to include formalization and separate validity attributes
  // Step = {
  //   symbol: string
  //   proposition: string
  //   justifiers: string[]
  //   truth: string
  //   valid_content: string    // Validity from content evaluation
  //   valid_formal: string     // Validity from formal evaluation
  //   formalization?: string   // Formal logic representation
  // }
  
  // Task-specific data
  task_data: {
    target_type: 'argument' | 'proposition'
    target_content: string  // proposition text if target_type is 'proposition', undefined if 'argument'
  }
  
  // Metadata
  metadata: {
    triggered_by: 'user_action' | 'agent_cascade' | 'scheduled' | 'manual'
    trigger_source: string
    timestamp: number
    ttl_seconds: number
  }
}
```

### Implementation
- Update Step model to include formalization attribute
- Implement agent input filtering (formalization omitted for content evaluation, content omitted for formal evaluation)
- Standardize all agent entry points
- Add validation and transformation logic

## 2. Agent Type Reorganization

### Problem
Current agents have overlapping responsibilities and unclear boundaries:
- `builder` and `rewriter` both modify propositions
- `content_evaluator` and `form_evaluator` both evaluate
- No clear specialization or hierarchy

### Required Agent Functions
Based on analysis of argumentation needs, agents must perform these specific functions:

1. **Evaluate truth of propositions**
   - Only those which were not evaluated in previous snapshot

2. **Evaluate validity of inferences**
   - Only those inferences which were not evaluated in previous snapshot
   - An inference from P, Q to R is equivalent to the evaluation of the truth of "if P and Q then R" where the conditional is strict implication, not material implication

3. **Check coherence**
   - Flag sets of incoherent propositions
   - That a set of propositions P, Q is incoherent is equivalent to the truth of "if P and Q then False" where the conditional is strict implication, not material implication

4. **Identify weakest inferences in argument**
   - Inferences whose validity, that is whose corresponding strict implication conditional are not absolutely true, are weakly valid

5. **Identify missing premises**
   - The additional premise with which a weakly valid inference would be stronger is a missing premise

6. **Recommend proposition rewriting and step reordering**
   - Recommend individual propositions rewrites
   - Recommend separating composite propositions into multiple simple propositions to make inferences explicit
   - Recommend combining simple propositions into composites for clarity
   - Recommend rewrites that serve formalization

7. **Formalize argument**
   - Select logical complexity: propositional, predicates, quantifiers, modes
   - Select predicates and names common to multiple propositions in view of potential for inference
   - Formalize all propositions holistically

8. **Formalize propositions**
   - Formalize only new propositions
   - Maintain consistency of predicates and names with previous snapshot

9. **Evaluate validity of formal inferences**
   - Do the same as 2, 3, 4, and 5 above, but only with respect to the formalizations of 7 and 8
   - Unlike 1-8, this task must not be passed full context; content is omitted to avoid distraction

### Solution: New Agent Taxonomy

#### **Core Agent Types**

**1. Content Evaluation Agent** (Evaluates truth, validity, coherence, and identifies weak inferences in natural language content)
```typescript
interface ContentEvaluationAgent {
  input: AgentInput  // Receives steps without formalization attributes
  output: ContentEvaluationResult[]
}
```

**2. Formal Evaluation Agent** (Evaluates validity of formalized logic)
```typescript
interface FormalEvaluationAgent {
  input: AgentInput  // Receives steps without natural language content
  output: FormalEvaluationResult[]
}
```

**3. Formalization Agent** (Converts natural language to formal logic)
```typescript
interface FormalizationAgent {
  input: AgentInput
  output: FormalizationResult[]
}
```

**4. Improvement Agent** (Recommends enhancements and restructuring)
```typescript
interface ImprovementAgent {
  input: AgentInput
  output: ImprovementResult[]
}
```

#### **Agent Hierarchy and Dependencies**
```
Content Evaluation Agent
├── Evaluates truth of propositions
├── Evaluates validity of natural language inferences
├── Checks coherence of proposition sets
└── Identifies weak inferences in natural language

Formalization Agent
├── Formalizes individual propositions
└── Formalizes entire arguments holistically

Formal Evaluation Agent (depends on: Formalization Agent)
├── Evaluates validity of formalized inferences
├── Checks coherence of formalized propositions
└── Identifies weakest formal inferences

Improvement Agent (depends on: Content Evaluation Agent)
├── Recommends proposition rewrites and restructuring
├── Recommends step reordering and restructuring
└── Identifies missing premises for weak inferences
```

## 3. Trigger Mechanism Rearchitecture

### Problem
Current triggering is reactive only to argument changes, limiting agent autonomy and continuous improvement. Agents work in isolation without considering the full context of previous results and related documents.

### Solution: Adaptive Context-Aware Trigger System

#### **Context-Aware Agent Input**
```typescript
interface ContextAwareAgentInput extends AgentInput {
  // Full context including all previous agent results
  context: {
    assumptions: Step[]
    argument: Step[]
    file_ids: string[]
    user_preferences: UserPreferences
    previous_agent_results: AgentResult[]  // Results from all previous agent runs
    document_context: DocumentContext[]    // Extracted content from PDFs and other files
  }
  
  // Agent decision making
  agent_decisions: {
    can_trigger_other_agents: boolean
    can_revisit_previous_work: boolean
    can_use_document_context: boolean
  }
}
```

#### **Document Context Integration**
```typescript
interface DocumentContext {
  file_id: string
  filename: string
  extracted_content: string
  relevance_score: number
  sections: DocumentSection[]
}

interface DocumentSection {
  content: string
  page_number: number
  relevance_to_argument: number
  key_concepts: string[]
}
```

#### **Direct Agent Handoff via Tool Calling**
```typescript
interface AgentTool {
  name: string
  description: string
  parameters: {
    type: "object"
    properties: {
      agent_type: { type: "string" }
      target_content: { type: "string" }
      context: { type: "object" }
      reasoning: { type: "string" }
    }
    required: ["agent_type", "reasoning"]
  }
}

// Each agent has access to tools for calling other agents
const agentTools = [
  {
    name: "trigger_content_evaluation",
    description: "Hand off to content evaluation agent for truth, validity, and coherence analysis",
    parameters: {
      type: "object",
      properties: {
        target_content: { type: "string", description: "Content to evaluate" },
        context: { type: "object", description: "Full conversation context" },
        reasoning: { type: "string", description: "Why this evaluation is needed" }
      },
      required: ["reasoning"]
    }
  },
  {
    name: "trigger_formalization", 
    description: "Hand off to formalization agent to convert natural language to formal logic",
    parameters: {
      type: "object",
      properties: {
        target_content: { type: "string", description: "Content to formalize" },
        context: { type: "object", description: "Full conversation context" },
        reasoning: { type: "string", description: "Why formalization is needed" }
      },
      required: ["reasoning"]
    }
  },
  {
    name: "trigger_formal_evaluation",
    description: "Hand off to formal evaluation agent for logical validity analysis",
    parameters: {
      type: "object", 
      properties: {
        target_content: { type: "string", description: "Formalized content to evaluate" },
        context: { type: "object", description: "Full conversation context" },
        reasoning: { type: "string", description: "Why formal evaluation is needed" }
      },
      required: ["reasoning"]
    }
  },
  {
    name: "trigger_improvement",
    description: "Hand off to improvement agent for recommendations and restructuring",
    parameters: {
      type: "object",
      properties: {
        target_content: { type: "string", description: "Content to improve" },
        context: { type: "object", description: "Full conversation context" },
        reasoning: { type: "string", description: "Why improvement is needed" }
      },
      required: ["reasoning"]
    }
  }
]
```

#### **Agent Handoff Coordinator**
```typescript
class AgentHandoffCoordinator {
  // Track agent call chains to prevent infinite loops
  private callChains: Map<string, string[]> = new Map()
  
  // Handle direct agent handoffs
  async handleAgentHandoff(
    fromAgent: string, 
    toAgent: string, 
    context: ContextAwareAgentInput,
    reasoning: string
  ): Promise<void> {
    // Check for infinite loops
    const callChain = this.callChains.get(context.conversation_id) || []
    if (this.wouldCreateLoop(callChain, toAgent)) {
      return // Prevent the handoff
    }
    
    // Update call chain
    this.callChains.set(context.conversation_id, [...callChain, toAgent])
    
    // Execute the handoff
    await this.executeAgent(toAgent, context, reasoning)
  }
  
  // Check iteration limits
  private wouldCreateLoop(callChain: string[], nextAgent: string): boolean {
    // Simple loop detection - could be more sophisticated
    return callChain.length > 10 || callChain.includes(nextAgent)
  }
  
  // Execute agent with full context
  private async executeAgent(
    agentType: string, 
    context: ContextAwareAgentInput,
    reasoning: string
  ): Promise<void> {
    // Agent gets full context including previous results and documents
    // Agent can make tool calls to other agents
    // Results are accumulated in the conversation context
    
    // TODO: Need to resolve conflict between full context handoff and content filtering
    // - Content Evaluation Agent: needs natural language but should NOT see formalizations
    // - Formal Evaluation Agent: needs formalizations but should NOT see natural language content
    // - Direct handoff requires full context to be passed between agents
    // Potential solutions:
    // 1. Context filtering in handoff coordinator
    // 2. Separate context objects for different agent types
    // 3. Agent-specific handoff tools with filtered context
  }
}
```

#### **Agent Decision Making**
```typescript
interface AgentHandoffDecision {
  agent_type: string
  reasoning: string
  target_content: string
  confidence: number
  expected_outcome: string
}
```

## 4. Snapshot Association

### Problem
Agents currently only associate with conversations, missing the rich context of conversation history and evolution. Managing full historical context is complex and may be excessive.

### Solution: Stale Results Propagation System

#### **Stale Results Propagation**
```typescript
interface SnapshotWithStaleResults {
  snapshot_id: string
  conversation_id: string
  
  // Current state
  assumptions: Step[]
  argument: Step[]
  
  // Stale results from previous snapshot (marked for replacement)
  stale_results: {
    content_evaluation: AgentResult[]  // Marked as stale
    formalization: AgentResult[]       // Marked as stale  
    formal_evaluation: AgentResult[]   // Marked as stale
    improvement: AgentResult[]         // Marked as stale
  }
  
  // Metadata
  created_at: number
  last_modified: number
  version: number
}

interface StaleResult {
  original_result: AgentResult
  marked_stale_at: number
  replacement_priority: number  // Higher priority = replace first
}

interface StaleResultsPropagation {
  // When user makes changes, copy previous agent results as stale
  copyStaleResults(fromSnapshot: ConversationSnapshot, toSnapshot: ConversationSnapshot): void
  
  // Agents replace stale results rather than filling in empty space
  replaceStaleResults(agentType: string, newResults: AgentResult[]): void
  
  // Benefits:
  // - No need for complex historical context
  // - Agents work on replacement rather than completion
  // - Simpler state management
  // - Handles rapid user changes naturally
}
```

## 5. TTL Implementation

### Problem
Agent results persist indefinitely, leading to stale data and resource waste.

### Solution: Multi-Level TTL System

#### **TTL Configuration**
```typescript
interface TTLConfig {
  // Result-level TTLs
  result_ttls: {
    discovery_results: number  // seconds
    analysis_results: number
    formalization_results: number
    improvement_results: number
    synthesis_results: number
  }
  
  // Context-level TTLs
  context_ttls: {
    snapshot_context: number
    file_context: number
    user_preferences: number
  }
  
  // Agent-level TTLs
  agent_ttls: {
    agent_session: number
    agent_memory: number
    agent_cache: number
  }
}
```

#### **TTL Management System**
```typescript
class TTLManager {
  // Result expiration
  scheduleResultExpiration(result_id: string, ttl_seconds: number): void
  extendResultTTL(result_id: string, extension_seconds: number): void
  cleanupExpiredResults(): void
  
  // Context expiration
  scheduleContextExpiration(context_id: string, ttl_seconds: number): void
  refreshContextTTL(context_id: string): void
  
  // Agent session management
  scheduleAgentSessionExpiration(agent_id: string, ttl_seconds: number): void
  keepAgentSessionAlive(agent_id: string): void
}
```

#### **TTL-Aware Result Storage**
```typescript
interface TTLResult {
  id: string
  data: any
  created_at: number
  expires_at: number
  ttl_seconds: number
  auto_extend: boolean
  extension_conditions: ExtensionCondition[]
}

interface ExtensionCondition {
  type: 'user_activity' | 'agent_activity' | 'relevance_threshold'
  condition_data: any
  extension_seconds: number
}
```

#### **Implementation Features**
1. **Automatic Cleanup**: Background process removes expired results
2. **Smart Extensions**: TTLs extend based on user activity and relevance
3. **Graceful Degradation**: Expired results marked as stale but not immediately deleted
4. **User Control**: Users can manually extend or expire results

## 6. Frontend Integration

### Problem
Frontend has limited integration with the agent system, showing only basic results.

### Solution: Rich Agent-Frontend Integration

#### **Enhanced Agent Results Display**
```typescript
interface EnhancedAgentResult {
  id: string
  agent_type: string
  operation: string
  
  // Rich result data
  result_data: {
    suggestions: AgentSuggestion[]
    analyses: AnalysisResult[]
    formalizations: FormalizationResult[]
    improvements: ImprovementResult[]
    synthesis: SynthesisResult[]
  }
  
  // Interactive elements
  interactions: {
    can_approve: boolean
    can_reject: boolean
    can_modify: boolean
    can_apply: boolean
  }
  
  // Metadata
  metadata: {
    confidence: number
    reasoning: string
    created_at: number
    expires_at: number
    relevance_score: number
  }
}
```

#### **Agent Status Dashboard**
```typescript
interface AgentStatusDashboard {
  // Active agents
  active_agents: {
    agent_type: string
    status: 'running' | 'pending' | 'completed' | 'failed'
    progress: number
    estimated_completion: number
  }[]
  
  // Recent results
  recent_results: EnhancedAgentResult[]
  
  // System health
  system_health: {
    queue_size: number
    average_response_time: number
    error_rate: number
    resource_usage: ResourceUsage
  }
}
```

#### **Interactive Agent Controls**
```typescript
interface AgentControls {
  // Manual triggering
  triggerAgent(agent_type: string, target: string): Promise<void>
  
  // Result management
  approveResult(result_id: string): Promise<void>
  rejectResult(result_id: string): Promise<void>
  modifyResult(result_id: string, modifications: any): Promise<void>
  
  // TTL management
  extendResultTTL(result_id: string, extension_seconds: number): Promise<void>
  expireResult(result_id: string): Promise<void>
  
  // Agent configuration
  configureAgent(agent_type: string, config: AgentConfig): Promise<void>
  pauseAgent(agent_type: string): Promise<void>
  resumeAgent(agent_type: string): Promise<void>
}
```

#### **Real-Time Updates**
```typescript
interface AgentRealTimeUpdates {
  // WebSocket events
  onAgentStarted(agent_id: string, agent_type: string): void
  onAgentCompleted(agent_id: string, result: EnhancedAgentResult): void
  onAgentFailed(agent_id: string, error: string): void
  
  // Result updates
  onResultExpired(result_id: string): void
  onResultExtended(result_id: string, new_expiry: number): void
  
  // System updates
  onSystemHealthUpdate(health: SystemHealth): void
  onQueueUpdate(queue_size: number): void
}
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
1. Implement `AgentInput` schema with context filtering
2. Update `Step` model to include `formalization`, `valid_content`, and `valid_formal` attributes
3. Set up `TTLManager` infrastructure
4. Implement `StaleResultsPropagation` system

### Phase 2: Agent Reorganization (Weeks 3-4)
1. Implement new agent taxonomy (Content Evaluation, Formalization, Formal Evaluation, Improvement)
2. Migrate existing agents to new types with proper input filtering
3. Set up direct agent handoff via OpenAI tool calling
4. Create `AgentHandoffCoordinator` with loop prevention

### Phase 3: Advanced Features (Weeks 5-6)
1. Implement document context integration for PDFs and files
2. Add context-aware agent decision making
3. Enhance TTL system with smart extensions
4. Resolve content filtering vs. full context handoff conflict

### Phase 4: Frontend Integration (Weeks 7-8)
1. Create enhanced result display components with stale result indicators
2. Implement agent status dashboard with real-time handoff tracking
3. Add interactive agent controls for manual triggering
4. Set up WebSocket-based real-time updates

### Phase 5: Testing and Optimization (Weeks 9-10)
1. Comprehensive testing of agent handoff chains and loop prevention
2. Performance optimization of context filtering and stale result propagation
3. User experience refinement with progressive disclosure
4. Documentation and training materials

## Success Metrics

### Technical Metrics
- **Response Time**: Agent response time < 5 seconds for 95% of requests
- **Accuracy**: Agent suggestion accuracy > 80% user approval rate
- **Resource Usage**: < 50% increase in memory/CPU usage
- **Reliability**: < 1% error rate for agent operations

### User Experience Metrics
- **Engagement**: 50% increase in user interaction with agent suggestions
- **Satisfaction**: 4.5+ star rating for agent functionality
- **Efficiency**: 30% reduction in time to complete arguments
- **Discovery**: 40% increase in users discovering new argument elements

### System Health Metrics
- **TTL Effectiveness**: 90% of expired results properly cleaned up
- **Cascade Efficiency**: 80% of cascades complete within 30 seconds
- **Snapshot Relevance**: 85% of agent results relevant to current snapshot
- **Trigger Accuracy**: 90% of triggers result in useful agent activity

## Risk Mitigation

### Technical Risks
1. **Performance Impact**: Implement gradual rollout with monitoring
2. **Data Loss**: Comprehensive backup and rollback procedures
3. **Complexity**: Modular implementation with clear interfaces
4. **Integration Issues**: Extensive testing and backward compatibility

### User Experience Risks
1. **Overwhelming Interface**: Progressive disclosure of advanced features
2. **Learning Curve**: Comprehensive onboarding and help system
3. **Unwanted Suggestions**: User control over agent activity levels
4. **Performance Perception**: Real-time feedback and progress indicators

## Conclusion

This rearchitecture plan transforms Dianoia's agent system from a reactive, conversation-focused system into a proactive, snapshot-aware, and user-controlled intelligent assistant. The phased implementation ensures minimal disruption while delivering significant improvements in functionality, performance, and user experience.

The new architecture provides:
- **Standardized Input**: Consistent data format across all agents
- **Clear Agent Roles**: Well-defined responsibilities and hierarchies
- **Flexible Triggering**: Multiple ways to activate agents based on needs
- **Rich Context**: Full awareness of conversation history and evolution
- **Efficient Resource Management**: Smart TTLs and cleanup
- **Enhanced User Experience**: Rich frontend integration and controls

This foundation enables future enhancements such as agent learning, collaborative agent networks, and advanced reasoning capabilities.
