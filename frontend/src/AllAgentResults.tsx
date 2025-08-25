import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import type { ConversationSnapshot } from './types'

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

type AgentResult = {
  agent_type: string
  operation: string
  result_content: any
  confidence: number
  reasoning: string
  processed_at: number
  target_metadata?: any
}

type AgentResultsProps = {
  conversationId: number
  sessionId: string
  snapshotVersion: number  // Required prop to track snapshot changes
  snapshotIndex: number  // Required prop for API calls
  getCurrentConversationState: () => { conversation: any, snapshotIndex: number }  // Function to get current conversation state
  saveSnapshotInPlace: (newSnap: ConversationSnapshot) => void
}

type ResultsByAgent = {
  [agentType: string]: AgentResult[]
}

export default function AllAgentResults({ conversationId, sessionId, snapshotVersion, snapshotIndex, getCurrentConversationState, saveSnapshotInPlace }: AgentResultsProps) {
  const [resultsByAgent, setResultsByAgent] = useState<ResultsByAgent>({})
  const [error, setError] = useState<string | null>(null)
  const [pollingKey, setPollingKey] = useState<number>(0) // Force useEffect re-run
  const tasksCompleteRef = useRef<boolean>(false)
  const currentPollingSnapshotRef = useRef<number>(-1)
  const intervalRef = useRef<number | null>(null)
  const currentFetchRef = useRef<Promise<void> | null>(null)

  // Helper function to get current snapshot
  const getCurrentSnapshot = () => {
    const { conversation, snapshotIndex: currentSnapshotIndex } = getCurrentConversationState()
    const lastSnapshot = conversation.snapshots[currentSnapshotIndex]
    return lastSnapshot || { assumptions: [], argument: [], explanation: '', file_ids: [] }
  }

  // Note: This component resets its state when snapshotIndex changes to ensure
  // proper behavior with undo/redo operations. Each snapshot will fetch its own
  // agent results independently.

  // Check if all formalizations are endorsed (for UI display purposes)
  const areAllFormalizationsEndorsed = () => {
    const currentSnapshot = getCurrentSnapshot()
    const allSteps = [...currentSnapshot.argument, ...currentSnapshot.assumptions]
    const stepsWithFormalizations = allSteps.filter((step: any) => step.formalization)
    
    if (stepsWithFormalizations.length === 0) return false
    
    return stepsWithFormalizations.every((step: any) => step.formalization?.endorsed)
  }

  // Trigger formal evaluator when user is ready
  const triggerFormalEvaluator = async () => {
    console.log('Triggering formal evaluator agent')
    
    try {
      const url = new URL(`${VITE_API_BASE_URL}/api/agents/evaluate-form`)
      url.searchParams.set('conversation_id', `${sessionId}:${conversationId}`)
      url.searchParams.set('snapshot_id', snapshotIndex.toString())
      
      const currentSnapshot = getCurrentSnapshot()
      const payload = {
        assumptions: currentSnapshot.assumptions,
        argument: currentSnapshot.argument,
        explanation: currentSnapshot.explanation,
        file_ids: currentSnapshot.file_ids
      }
      
      const response = await axios.post(url.toString(), payload)
      console.log('Formal evaluator agent triggered successfully:', response.data)
      
      // Reset polling state to start fetching results again
      tasksCompleteRef.current = false
      currentPollingSnapshotRef.current = -1 // Force restart of polling
      setResultsByAgent({})
      setError(null)
      setPollingKey(prev => prev + 1) // Force useEffect to re-run
    } catch (error: any) {
      if (error.response?.status === 400) {
        // Validation error - show specific message
        console.log('Formal evaluator validation failed:', error.response.data.detail)
      } else {
        console.error('Failed to trigger formal evaluator agent:', error)
      }
    }
  }

  // Apply agent results to argument steps
  const applyAgentResultsToSnapshot = (newResultsByAgent: ResultsByAgent) => {
    // Get the current conversation state to ensure we have the latest snapshot
    const currentSnapshot = getCurrentSnapshot()
    const updatedSnapshot = { 
      ...currentSnapshot,
      argument: [...currentSnapshot.argument], // Create new array
      assumptions: [...currentSnapshot.assumptions] // Create new array
    }
    let hasChanges = false

    // Apply ContentEvaluationAgent results
    const contentResults = newResultsByAgent['content_evaluator']
    if (contentResults && contentResults.length > 0) {
      const latestContentResult = contentResults[contentResults.length - 1]
      const resultContent = latestContentResult.result_content

      // Apply truth evaluations (only to argument steps, not assumptions)
      if (resultContent.truth_evaluations) {
        resultContent.truth_evaluations.forEach((evaluation: any) => {
          const stepIndex = updatedSnapshot.argument.findIndex((s: any) => s.symbol === evaluation.symbol)
          if (stepIndex !== -1) {
            const oldStep = updatedSnapshot.argument[stepIndex]
            // Create new step object to avoid read-only property error
            const newStep = {
              ...oldStep,
              truth: evaluation.truth_value.toString()
            }
            updatedSnapshot.argument[stepIndex] = newStep
            hasChanges = true
          }
        })
      }

      // Apply validity evaluations (only to argument steps, not assumptions)
      if (resultContent.validity_evaluations) {
        resultContent.validity_evaluations.forEach((evaluation: any) => {
          const stepIndex = updatedSnapshot.argument.findIndex((s: any) => s.symbol === evaluation.symbol)
          if (stepIndex !== -1) {
            const oldStep = updatedSnapshot.argument[stepIndex]
            // Create new step object to avoid read-only property error
            const newStep = {
              ...oldStep,
              valid: evaluation.validity_value.toString()
            }
            updatedSnapshot.argument[stepIndex] = newStep
            hasChanges = true
          }
        })
      }
    }

    // Apply FormalizationAgent results
    const formalizationResults = newResultsByAgent['formalizer']
    console.log('🔍 Formalization results:', formalizationResults)
    if (formalizationResults && formalizationResults.length > 0) {
      const latestFormalizationResult = formalizationResults[formalizationResults.length - 1]
      const resultContent = latestFormalizationResult.result_content
      console.log('🔍 Latest formalization result content:', resultContent)

      // Apply formalizations (but don't replace endorsed ones)
      if (resultContent.formalizations) {
        console.log('🔍 Applying formalizations:', resultContent.formalizations)
        resultContent.formalizations.forEach((formalization: any) => {
          const stepIndex = updatedSnapshot.argument.findIndex((s: any) => s.symbol === formalization.symbol)
          console.log('🔍 Looking for step with symbol:', formalization.symbol, 'found at index:', stepIndex)
          if (stepIndex !== -1) {
            const oldStep = updatedSnapshot.argument[stepIndex]
            
            // Skip if this step already has an endorsed formalization
            if (oldStep.formalization?.endorsed) {
              console.log('🔍 Skipping step with endorsed formalization:', formalization.symbol)
              return
            }
            
            // Create new step object to avoid read-only property error
            const newStep = {
              ...oldStep,
              formalization: {
                ascii: formalization.ascii,
                json_structure: typeof formalization.json_structure === 'string' 
                  ? JSON.parse(formalization.json_structure) 
                  : formalization.json_structure,
                endorsed: false
              }
            }
            updatedSnapshot.argument[stepIndex] = newStep
            hasChanges = true
            console.log('🔍 Applied formalization to step:', formalization.symbol)
          } else {
            console.log('🔍 Could not find step with symbol:', formalization.symbol)
          }
        })
      } else {
        console.log('🔍 No formalizations in result content')
      }

      // Save formalization definitions to snapshot
      if (resultContent.definitions) {
        updatedSnapshot.formalization_definitions = resultContent.definitions
        hasChanges = true
      }
    }

    // Save updated snapshot if there were changes
    if (hasChanges) {
      saveSnapshotInPlace(updatedSnapshot)
    }
  }

  const fetchResults = async () => {
    // Prevent concurrent fetches
    if (currentFetchRef.current) {
      console.log('⏭️ Skipping fetch - already in progress')
      return
    }
    
    console.log('🚀 Starting fetch - creating promise')
    
    // Clear the flag synchronously to prevent race conditions
    currentFetchRef.current = (async () => {
      try {
        const response = await axios.get(`${VITE_API_BASE_URL}/api/agents/results`, {
          params: {
            conversation_id: `${sessionId}:${conversationId}`,
            snapshot_id: String(snapshotIndex)
          },
          timeout: 5000 // 5 second timeout
        })
        
        console.log('📡 Response received:', response.status)
        const newResultsByAgent = response.data.results_by_agent || {}
        const newTasksComplete = response.data.tasks_complete || false
        
        console.log('📊 Agent results received:', {
          resultsByAgent: newResultsByAgent,
          tasksComplete: newTasksComplete,
          currentTasksComplete: tasksCompleteRef.current
        })
        
        // Only update if we have new results
        if (JSON.stringify(newResultsByAgent) !== JSON.stringify(resultsByAgent)) {
          console.log('🔄 Updating results - new data detected')
          setResultsByAgent(newResultsByAgent)
          // Apply results to snapshot
          applyAgentResultsToSnapshot(newResultsByAgent)
        } else {
          console.log('⏭️ Skipping update - no new data')
        }
        
        // Update tasks complete status
        if (newTasksComplete !== tasksCompleteRef.current) {
          console.log('✅ Tasks complete status changed:', { 
            from: tasksCompleteRef.current, 
            to: newTasksComplete 
          })
          tasksCompleteRef.current = newTasksComplete
          
          // Clear interval if tasks are complete
          if (newTasksComplete && intervalRef.current) {
            console.log('🛑 Clearing interval - tasks complete')
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
        
      } catch (error: any) {
        console.error('❌ Error fetching agent results:', error)
        setError('Error loading results')
      }
    })()
    
    // Wait for the promise to complete and then clear the flag
    await currentFetchRef.current
    console.log('🏁 Fetch completed - clearing promise reference')
    currentFetchRef.current = null
  }

  useEffect(() => {
    // Skip fetching if snapshotIndex is less than 1 (no snapshot history yet)
    if (snapshotIndex < 1) {
      console.log('⏭️ Skipping agent results fetch - no snapshot history yet:', { snapshotIndex })
      return
    }
    
    // Skip if we're already polling for this snapshot
    if (currentPollingSnapshotRef.current === snapshotIndex) {
      console.log('⏭️ Already polling for snapshot:', { snapshotIndex })
      return
    }
    
    console.log('🔄 useEffect triggered with dependencies:', { 
      conversationId, 
      sessionId, 
      snapshotVersion, 
      snapshotIndex
    })
    
    // Reset state when conversation or snapshot changes
    console.log('🔄 Resetting agent results state for new snapshot:', { snapshotIndex, snapshotVersion })
    setResultsByAgent({})
    setError(null)
    tasksCompleteRef.current = false
    currentPollingSnapshotRef.current = snapshotIndex
    
    // Set up polling every 1 second, but only if tasks are not complete
    const interval = setInterval(() => {
      console.log('⏰ Polling interval triggered - checking state:', { 
        tasksComplete: tasksCompleteRef.current, 
        isFetching: !!currentFetchRef.current, // Check if a fetch is in progress
        pollingSnapshot: snapshotIndex
      })
      
      if (!tasksCompleteRef.current) {
        if (!currentFetchRef.current) {
          console.log('⏰ Polling interval triggered - tasks not complete, starting fetch')
          fetchResults()
        } else {
          console.log('⏰ Polling interval triggered - tasks not complete, but fetch already in progress')
        }
      } else {
        console.log('⏹️ Polling interval triggered - tasks complete, skipping fetch')
      }
    }, 1000)
    
    // Store interval reference
    intervalRef.current = interval
    
    console.log('🚀 Started polling for agent results')
    
    return () => {
      console.log('🛑 Stopped polling for agent results')
      clearInterval(interval)
      intervalRef.current = null
    }
  }, [conversationId, sessionId, snapshotIndex, pollingKey]) // Added pollingKey to dependencies



  // Check if all formalizations are endorsed
  const allFormalizationsEndorsed = areAllFormalizationsEndorsed()

  // Don't show anything if no results
  if (Object.keys(resultsByAgent).length === 0) {
    return null
  }

  const renderBuilderResults = (results: AgentResult[]) => {
    return (
      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex justify-between items-start mb-3">
              <span className="font-medium text-blue-700 flex items-center">
                <span className="mr-2">🔨</span>
                Argument Builder
              </span>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {result.confidence.toFixed(2)} confidence
              </span>
            </div>
            <div className="text-sm text-gray-700 mb-3 p-2 bg-gray-50 rounded">
              💭 {result.reasoning}
            </div>
            {result.result_content?.justifications && result.result_content.justifications.length > 0 && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  💡 Suggested Justifications:
                </div>
                <ul className="space-y-2">
                  {result.result_content.justifications.map((justification: any, jIndex: number) => (
                    <li key={jIndex} className="text-sm text-gray-700 p-2 bg-green-50 rounded border border-green-200">
                      {justification.propositions?.join(', ') || 'No propositions'}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderContentEvaluatorResults = (results: AgentResult[]) => {
    return (
      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex justify-between items-start mb-3">
              <span className="font-medium text-purple-700 flex items-center">
                <span className="mr-2">🔍</span>
                Content Evaluator
              </span>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {result.confidence.toFixed(2)} confidence
              </span>
            </div>
            {result.result_content && (
              <div className="mt-3 space-y-2">
                {/* Truth Evaluations */}
                {result.result_content.truth_evaluations && result.result_content.truth_evaluations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      📊 Truth Evaluations:
                    </div>
                    <div className="space-y-1">
                      {result.result_content.truth_evaluations.map((evaluation: any, index: number) => (
                        <div key={index} className="text-sm p-2 bg-gray-50 rounded border border-gray-200">
                          <div className="flex justify-between items-start">
                            <span className="text-gray-700 flex-1">
                              <span className="font-medium">{evaluation.symbol}:</span> {evaluation.reasoning}
                            </span>
                            <span className={`font-medium ml-2 px-2 py-1 rounded text-xs ${
                              evaluation.truth_value >= 0.8 ? 'bg-green-100 text-green-800' :
                              evaluation.truth_value >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {(evaluation.truth_value * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Validity Evaluations */}
                {result.result_content.validity_evaluations && result.result_content.validity_evaluations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      🔗 Validity Evaluations:
                    </div>
                    <div className="space-y-1">
                      {result.result_content.validity_evaluations.map((evaluation: any, index: number) => (
                        <div key={index} className="text-sm p-2 bg-blue-50 rounded border border-blue-200">
                          <div className="flex justify-between items-start">
                            <span className="text-gray-700 flex-1">
                              <span className="font-medium">{evaluation.symbol}:</span> {evaluation.reasoning}
                            </span>
                            <span className={`font-medium ml-2 px-2 py-1 rounded text-xs ${
                              evaluation.validity_value >= 0.8 ? 'bg-green-100 text-green-800' :
                              evaluation.validity_value >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {(evaluation.validity_value * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Incoherent Sets */}
                {result.result_content.incoherent_sets && result.result_content.incoherent_sets.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-red-700 mb-2">
                      ⚠️ Incoherent Sets:
                    </div>
                    <div className="space-y-2">
                      {result.result_content.incoherent_sets.map((incoherentSet: any, iIndex: number) => (
                        <div key={iIndex} className="text-sm p-2 bg-red-50 rounded border border-red-200">
                          <div className="flex justify-between items-start">
                            <span className="text-red-700 flex-1">
                              <span className="font-medium">Steps {incoherentSet.symbols.join(', ')}:</span>
                              <span className="ml-2 text-xs">
                                {incoherentSet.incoherence_value === 1.0 ? 'Logical Contradiction' : 
                                 `Incoherence Level: ${(incoherentSet.incoherence_value * 100).toFixed(0)}%`}
                              </span>
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Logical Issues */}
                {result.result_content.logical_issues && result.result_content.logical_issues.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-red-700 mb-2">
                      ⚠️ Logical Issues:
                    </div>
                    <ul className="space-y-1">
                      {result.result_content.logical_issues.map((issue: string, iIndex: number) => (
                        <li key={iIndex} className="text-sm text-red-700 p-2 bg-red-50 rounded border border-red-200">
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Recommendations */}
                {result.result_content.recommendations && result.result_content.recommendations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-blue-700 mb-2">
                      💡 Recommendations:
                    </div>
                    <ul className="space-y-1">
                      {result.result_content.recommendations.map((rec: string, rIndex: number) => (
                        <li key={rIndex} className="text-sm text-blue-700 p-2 bg-blue-50 rounded border border-blue-200">
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderFormEvaluatorResults = (results: AgentResult[]) => {
    return (
      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex justify-between items-start mb-3">
              <span className="font-medium text-orange-700 flex items-center">
                <span className="mr-2">🧮</span>
                Formal Logic Evaluator
              </span>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {result.confidence.toFixed(2)} confidence
              </span>
            </div>
            <div className="text-sm text-gray-700 mb-3 p-2 bg-gray-50 rounded">
              💭 {result.reasoning}
            </div>
            
            {/* Argument Validity */}
            {result.result_content?.argument_validity !== undefined && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  🎯 Overall Argument Validity:
                </div>
                <div className={`inline-block px-3 py-1 rounded text-sm font-medium ${
                  result.result_content.argument_validity >= 0.8 ? 'bg-green-100 text-green-800' :
                  result.result_content.argument_validity >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {(result.result_content.argument_validity * 100).toFixed(0)}%
                </div>
              </div>
            )}

            {/* Proposition Evaluations */}
            {result.result_content?.proposition_evaluations && result.result_content.proposition_evaluations.length > 0 && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  📊 Proposition Validity Evaluations:
                </div>
                <div className="space-y-2">
                  {result.result_content.proposition_evaluations.map((evaluation: any, index: number) => (
                    <div key={index} className="p-2 bg-gray-50 rounded border border-gray-200">
                      <div className="flex justify-between items-start">
                        <span className="text-gray-700 flex-1">
                          <span className="font-medium">{evaluation.symbol}:</span> {evaluation.reasoning}
                        </span>
                        <span className={`font-medium ml-2 px-2 py-1 rounded text-xs ${
                          evaluation.validity >= 0.8 ? 'bg-green-100 text-green-800' :
                          evaluation.validity >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {(evaluation.validity * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Logical Issues */}
            {result.result_content?.logical_issues && result.result_content.logical_issues.length > 0 && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  ⚠️ Logical Issues:
                </div>
                <ul className="space-y-1">
                  {result.result_content.logical_issues.map((issue: string, index: number) => (
                    <li key={index} className="text-sm text-red-700 p-2 bg-red-50 rounded border border-red-200">
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {result.result_content?.recommendations && result.result_content.recommendations.length > 0 && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  💡 Recommendations:
                </div>
                <ul className="space-y-1">
                  {result.result_content.recommendations.map((recommendation: string, index: number) => (
                    <li key={index} className="text-sm text-blue-700 p-2 bg-blue-50 rounded border border-blue-200">
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }

  const renderFormalizerResults = (results: AgentResult[]) => {
    return (
      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex justify-between items-start mb-3">
              <span className="font-medium text-green-700 flex items-center">
                <span className="mr-2">📐</span>
                Formalization Agent
              </span>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {result.confidence.toFixed(2)} confidence
              </span>
            </div>
            {result.result_content?.definitions && (
              <div className="mt-3 space-y-2">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  📚 Definitions:
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {result.result_content.definitions.predicates.length > 0 && (
                    <div className="p-2 bg-blue-50 rounded border border-blue-200">
                      <div className="text-sm font-medium text-blue-700 mb-2">Predicates:</div>
                      <div className="space-y-1">
                        {result.result_content.definitions.predicates.map((pred: any) => (
                          <div key={pred.symbol} className="text-sm">
                            <span className="font-mono text-blue-800">{pred.symbol}</span>
                            <span className="text-gray-600"> = </span>
                            <span className="text-gray-700">{pred.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {result.result_content.definitions.constants.length > 0 && (
                    <div className="p-2 bg-purple-50 rounded border border-purple-200">
                      <div className="text-sm font-medium text-purple-700 mb-2">Constants:</div>
                      <div className="space-y-1">
                        {result.result_content.definitions.constants.map((constDef: any) => (
                          <div key={constDef.symbol} className="text-sm">
                            <span className="font-mono text-purple-800">{constDef.symbol}</span>
                            <span className="text-gray-600"> = </span>
                            <span className="text-gray-700">{constDef.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
            {result.result_content?.formalizations && result.result_content.formalizations.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  📐 Formalizations:
                </div>
                <div className="space-y-2">
                  {result.result_content.formalizations.map((formalization: any, fIndex: number) => (
                    <div key={fIndex} className="p-2 bg-green-50 rounded border border-green-200">
                      <div className="flex justify-between items-start">
                        <span className="text-sm font-medium text-gray-700">
                          Step {formalization.symbol}:
                        </span>
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          ASCII
                        </span>
                      </div>
                      <div className="text-sm font-mono text-gray-800 mt-1">
                        {formalization.ascii}
                      </div>
                      {formalization.json_structure && Object.keys(formalization.json_structure).length > 0 && (
                        <div className="mt-2">
                          <div className="text-xs text-gray-500 mb-1">JSON Structure:</div>
                          <div className="text-xs font-mono text-gray-700 bg-white p-2 rounded border overflow-x-auto">
                            <pre className="whitespace-pre-wrap">{JSON.stringify(formalization.json_structure, null, 2)}</pre>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    )
  }



  return (
    <div className="mt-4 space-y-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800">🤖 Agent Suggestions & Evaluations</h3>
      
      {/* Formalization Status and Trigger */}
      {allFormalizationsEndorsed && (
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <span className="text-green-700 mr-2">✅</span>
              <span className="text-green-800 font-medium">All formalizations endorsed</span>
            </div>
            <button
              onClick={triggerFormalEvaluator}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm font-medium"
            >
              🧮 Run Formal Evaluation
            </button>
          </div>
          <p className="text-green-700 text-sm mt-2">
            Ready to evaluate the logical validity of your formalized argument.
          </p>
        </div>
      )}
      {error && (
        <div className="text-red-600 mb-2 p-2 bg-red-50 rounded border border-red-200">
          Error loading results: {error}
        </div>
      )}
      
      {Object.entries(resultsByAgent).map(([agentType, results]) => (
        <div key={agentType} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h4 className="text-md font-semibold mb-3 text-gray-800">
            {agentType === 'builder' && '🔨 Argument Builder'}
            {agentType === 'content_evaluator' && '🔍 Content Evaluator'}
            {agentType === 'form_evaluator' && '🧮 Formal Logic Evaluator'}
            {agentType === 'formalizer' && '📐 Formalization Agent'}
            {agentType === 'rewriter' && '✏️ Rewriter Agent'}
          </h4>
          
          {agentType === 'builder' && renderBuilderResults(results)}
          {agentType === 'content_evaluator' && renderContentEvaluatorResults(results)}
          {agentType === 'form_evaluator' && renderFormEvaluatorResults(results)}
          {agentType === 'formalizer' && renderFormalizerResults(results)}
        </div>
      ))}
    </div>
  )
} 