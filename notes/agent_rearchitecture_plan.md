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
- Standardize all agent entry points
- Add validation and transformation logic

## 2. Agent Type Reorganization

### Problem
Current agents have overlapping responsibilities and unclear boundaries:
- `builder` and `rewriter` both modify propositions
- `content_evaluator` and `form_evaluator` both evaluate
- No clear specialization or hierarchy

### Solution: New Agent Taxonomy

#### **Core Agent Types**

**1. Discovery Agents** (Find and suggest content)
```typescript
interface DiscoveryAgent {
  type: 'proposition_discovery' | 'argument_discovery' | 'counter_argument_discovery'
  capabilities: ['suggest_propositions', 'identify_gaps', 'find_evidence']
  input: AgentInput
  output: DiscoveryResult[]
}
```

**2. Analysis Agents** (Evaluate and assess)
```typescript
interface AnalysisAgent {
  type: 'truth_analysis' | 'validity_analysis' | 'coherence_analysis' | 'completeness_analysis'
  capabilities: ['evaluate_truth', 'assess_validity', 'check_coherence', 'identify_missing_premises']
  input: AgentInput
  output: AnalysisResult[]
}
```

**3. Formalization Agents** (Convert to formal logic)
```typescript
interface FormalizationAgent {
  type: 'proposition_formalization' | 'argument_formalization' | 'proof_formalization'
  capabilities: ['formalize_proposition', 'formalize_argument', 'generate_proof_sketch']
  input: AgentInput
  output: FormalizationResult[]
}
```

**4. Improvement Agents** (Enhance and refine)
```typescript
interface ImprovementAgent {
  type: 'proposition_improvement' | 'argument_restructuring' | 'clarity_enhancement'
  capabilities: ['rewrite_proposition', 'restructure_argument', 'improve_clarity']
  input: AgentInput
  output: ImprovementResult[]
}
```

**5. Synthesis Agents** (Combine and integrate)
```typescript
interface SynthesisAgent {
  type: 'argument_synthesis' | 'evidence_synthesis' | 'conclusion_synthesis'
  capabilities: ['synthesize_arguments', 'combine_evidence', 'draw_conclusions']
  input: AgentInput
  output: SynthesisResult[]
}
```

#### **Agent Hierarchy and Dependencies**
```
Discovery Agents
├── Proposition Discovery
├── Argument Discovery
└── Counter-Argument Discovery

Analysis Agents
├── Truth Analysis (depends on: Proposition Discovery)
├── Validity Analysis (depends on: Formalization Agents)
├── Coherence Analysis (depends on: Argument Discovery)
└── Completeness Analysis (depends on: Discovery Agents)

Formalization Agents
├── Proposition Formalization
├── Argument Formalization
└── Proof Formalization

Improvement Agents
├── Proposition Improvement (depends on: Analysis Agents)
├── Argument Restructuring (depends on: Analysis Agents)
└── Clarity Enhancement (depends on: Analysis Agents)

Synthesis Agents
├── Argument Synthesis (depends on: All other agents)
├── Evidence Synthesis (depends on: Discovery Agents)
└── Conclusion Synthesis (depends on: Analysis Agents)
```

## 3. Trigger Mechanism Rearchitecture

### Problem
Current triggering is reactive only to argument changes, limiting agent autonomy and continuous improvement.

### Solution: Multi-Modal Trigger System

#### **Trigger Types**

**1. Event-Driven Triggers**
```typescript
interface EventTrigger {
  type: 'user_action' | 'agent_completion' | 'snapshot_change' | 'file_upload'
  event_data: any
  priority: 'immediate' | 'high' | 'normal' | 'low'
  cascade_rules: CascadeRule[]
}
```

**2. Time-Based Triggers**
```typescript
interface TimeTrigger {
  type: 'periodic' | 'delayed' | 'scheduled'
  interval_seconds: number
  conditions: TriggerCondition[]
  max_executions: number
}
```

**3. Condition-Based Triggers**
```typescript
interface ConditionTrigger {
  type: 'state_change' | 'threshold_reached' | 'dependency_met'
  conditions: TriggerCondition[]
  evaluation_frequency: number
}
```

#### **Trigger Coordinator**
```typescript
class TriggerCoordinator {
  // Event-driven triggers
  onUserAction(action: UserAction): void
  onAgentCompletion(completion: AgentCompletion): void
  onSnapshotChange(change: SnapshotChange): void
  
  // Time-based triggers
  schedulePeriodicTask(agent_type: string, interval: number): void
  scheduleDelayedTask(agent_type: string, delay: number): void
  
  // Condition-based triggers
  evaluateConditions(snapshot: ConversationSnapshot): void
  
  // Cascade management
  executeCascade(trigger: EventTrigger): void
}
```

#### **Cascade Rules**
```typescript
interface CascadeRule {
  source_agent: string
  target_agents: string[]
  conditions: CascadeCondition[]
  delay_seconds: number
  priority: number
}

// Example cascade: When formalization completes, trigger validity analysis
{
  source_agent: 'proposition_formalization',
  target_agents: ['validity_analysis'],
  conditions: [{ type: 'formalization_complete', confidence_threshold: 0.7 }],
  delay_seconds: 0,
  priority: 1
}
```

## 4. Snapshot Association

### Problem
Agents currently only associate with conversations, missing the rich context of conversation history and evolution.

### Solution: Snapshot-Aware Agent System

#### **Snapshot Context Model**
```typescript
interface SnapshotContext {
  snapshot_id: string
  conversation_id: string
  
  // Current state
  assumptions: Step[]
  argument: Step[]
  
  // Historical context (managed by server)
  previous_snapshots: ConversationSnapshot[]
  snapshot_diffs: SnapshotDiff[]
  
  // Evolution tracking
  change_history: SnapshotChange[]
  agent_contribution_history: AgentContribution[]
  
  // Metadata
  created_at: number
  last_modified: number
  version: number
}

interface SnapshotDiff {
  from_snapshot_id: string
  to_snapshot_id: string
  changes: {
    propositions_added: string[]
    propositions_removed: string[]
    propositions_modified: string[]
    assumptions_changed: boolean
    argument_structure_changed: boolean
  }
}
```

#### **Agent-Snapshot Association**
```typescript
interface AgentSnapshotAssociation {
  agent_id: string
  snapshot_id: string
  conversation_id: string
  
  // Association metadata
  association_type: 'primary' | 'secondary' | 'historical'
  relevance_score: number
  last_activity: number
  
  // Context awareness
  understands_history: boolean
  can_access_previous_snapshots: boolean
  tracks_evolution: boolean
}
```

#### **Implementation Strategy**
1. **Snapshot-Aware Input**: All agent inputs include snapshot context
2. **Historical Analysis**: Agents can analyze conversation evolution
3. **Predictive Suggestions**: Agents use history to predict future improvements
4. **Contextual Relevance**: Results are scored based on snapshot relevance

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
1. Implement `AgentInput` schema
2. Set up `TTLManager` infrastructure
3. Add snapshot context to existing agents

### Phase 2: Agent Reorganization (Weeks 3-4)
1. Implement new agent taxonomy
2. Migrate existing agents to new types
3. Set up agent hierarchy and dependencies
4. Create `TriggerCoordinator`

### Phase 3: Advanced Features (Weeks 5-6)
1. Implement cascade rules
2. Add condition-based triggers
3. Enhance TTL system with smart extensions
4. Add snapshot evolution tracking

### Phase 4: Frontend Integration (Weeks 7-8)
1. Create enhanced result display components
2. Implement agent status dashboard
3. Add interactive agent controls
4. Set up real-time updates

### Phase 5: Testing and Optimization (Weeks 9-10)
1. Comprehensive testing of all components
2. Performance optimization
3. User experience refinement
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
