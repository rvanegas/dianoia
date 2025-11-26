import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

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
  snapshotVersion?: number  // Add prop to track snapshot changes
}

type ResultsByAgent = {
  [agentType: string]: AgentResult[]
}

export default function AllAgentResults({ conversationId, sessionId, snapshotVersion }: AgentResultsProps) {
  const [resultsByAgent, setResultsByAgent] = useState<ResultsByAgent>({})
  const [error, setError] = useState<string | null>(null)
  const tasksCompleteRef = useRef<boolean>(false)

  const fetchResults = async () => {
    try {
      const url = new URL(`${VITE_API_BASE_URL}/api/agents/results`)
      url.searchParams.set('conversation_id', `${sessionId}:${conversationId}`)
      
      const response = await axios.get(url.toString())
      
      const newResultsByAgent = response.data.results_by_agent || {}
      const newTasksComplete = response.data.tasks_complete || false
      
      // Only update if we have new results
      if (JSON.stringify(newResultsByAgent) !== JSON.stringify(resultsByAgent)) {
        setResultsByAgent(newResultsByAgent)
      }
      
      // Update tasks complete status
      tasksCompleteRef.current = newTasksComplete
      setError(null)
    } catch (err: any) {
      console.error('Error fetching agent results:', err)
      setError(err.message)
    }
  }

  useEffect(() => {
    // Reset tasks complete status when conversation or snapshot changes
    tasksCompleteRef.current = false
    
    // Set up polling every 2 seconds, but only if tasks are not complete
    const interval = setInterval(() => {
      if (!tasksCompleteRef.current) {
        fetchResults()
      }
    }, 2000)
    
    return () => {
      clearInterval(interval)
    }
  }, [conversationId, sessionId, snapshotVersion]) // Removed tasksComplete from dependencies

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
            <div className="text-sm text-gray-700 mb-3 p-2 bg-gray-50 rounded">
              💭 {result.reasoning}
            </div>
            {result.result_content?.evaluation && (
              <div className="mt-3 space-y-2">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-blue-50 p-2 rounded">
                    <span className="font-medium">Validity:</span> {(result.result_content.evaluation.argument_validity * 100).toFixed(0)}%
                  </div>
                </div>
                {result.result_content.evaluation.proposition_evaluations && result.result_content.evaluation.proposition_evaluations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      📊 Proposition Truth Values:
                    </div>
                    <div className="space-y-1">
                      {result.result_content.evaluation.proposition_evaluations.map((prop: any, pIndex: number) => (
                        <div key={pIndex} className="text-sm p-2 bg-gray-50 rounded border border-gray-200">
                          <div className="flex justify-between items-start">
                            <span className="text-gray-700 flex-1">{prop.proposition}</span>
                            <span className={`font-medium ml-2 px-2 py-1 rounded text-xs ${
                              prop.truth_value >= 0.8 ? 'bg-green-100 text-green-800' :
                              prop.truth_value >= 0.5 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {(prop.truth_value * 100).toFixed(0)}%
                            </span>
                          </div>
                          {prop.reasoning && (
                            <div className="text-xs text-gray-500 mt-1 italic">
                              {prop.reasoning}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {result.result_content.evaluation.logical_issues && result.result_content.evaluation.logical_issues.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-red-700 mb-2">
                      ⚠️ Logical Issues:
                    </div>
                    <ul className="space-y-1">
                      {result.result_content.evaluation.logical_issues.map((issue: string, iIndex: number) => (
                        <li key={iIndex} className="text-sm text-red-700 p-2 bg-red-50 rounded border border-red-200">
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {result.result_content.evaluation.recommendations && result.result_content.evaluation.recommendations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-blue-700 mb-2">
                      💡 Recommendations:
                    </div>
                    <ul className="space-y-1">
                      {result.result_content.evaluation.recommendations.map((rec: string, rIndex: number) => (
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
            {result.result_content?.evaluation && (
              <div className="mt-3 space-y-2">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-orange-50 p-2 rounded border border-orange-200">
                    <span className="font-medium">Formal Validity:</span> {(result.result_content.evaluation.argument_validity * 100).toFixed(0)}%
                  </div>
                </div>
                {result.result_content.evaluation.proposition_evaluations && result.result_content.evaluation.proposition_evaluations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      📐 Formal Proposition Analysis:
                    </div>
                    <div className="space-y-1">
                      {result.result_content.evaluation.proposition_evaluations.map((prop: any, pIndex: number) => (
                        <div key={pIndex} className="text-sm p-2 bg-orange-50 rounded border border-orange-200">
                          <div className="flex justify-between items-start">
                            <span className="text-gray-700 flex-1">{prop.proposition}</span>
                            <span className="font-medium ml-2 px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                              Neither true nor false by form alone
                            </span>
                          </div>
                          {prop.reasoning && (
                            <div className="text-xs text-gray-500 mt-1 italic">
                              {prop.reasoning}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {result.result_content.evaluation.logical_issues && result.result_content.evaluation.logical_issues.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-red-700 mb-2">
                      ⚠️ Formal Logic Issues:
                    </div>
                    <ul className="space-y-1">
                      {result.result_content.evaluation.logical_issues.map((issue: string, iIndex: number) => (
                        <li key={iIndex} className="text-sm text-red-700 p-2 bg-red-50 rounded border border-red-200">
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {result.result_content.evaluation.recommendations && result.result_content.evaluation.recommendations.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-orange-700 mb-2">
                      💡 Formal Logic Recommendations:
                    </div>
                    <ul className="space-y-1">
                      {result.result_content.evaluation.recommendations.map((rec: string, rIndex: number) => (
                        <li key={rIndex} className="text-sm text-orange-700 p-2 bg-orange-50 rounded border border-orange-200">
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
            <div className="text-sm text-gray-700 mb-3 p-2 bg-gray-50 rounded">
              💭 {result.reasoning}
            </div>
            {result.result_content?.proposition && (
              <div className="mt-3 space-y-2">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  📝 Original Proposition:
                </div>
                <div className="text-sm text-gray-700 p-2 bg-blue-50 rounded border border-blue-200">
                  {result.result_content.proposition}
                </div>
                {result.result_content.ascii && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      🔤 ASCII Formalization:
                    </div>
                    <div className="text-sm font-mono text-gray-800 p-2 bg-green-50 rounded border border-green-200">
                      {result.result_content.ascii}
                    </div>
                  </div>
                )}
                {result.result_content.json && Object.keys(result.result_content.json).length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      🏗️ JSON Structure:
                    </div>
                    <div className="text-sm font-mono text-gray-800 p-2 bg-purple-50 rounded border border-purple-200 overflow-x-auto">
                      <pre className="whitespace-pre-wrap">{JSON.stringify(result.result_content.json, null, 2)}</pre>
                    </div>
                  </div>
                )}
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