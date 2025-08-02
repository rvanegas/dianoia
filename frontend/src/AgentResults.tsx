import { useState, useEffect } from 'react'
import axios from 'axios'

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

type AgentResult = {
  agent_type: string
  operation: string
  data: any
  confidence: number
  reasoning: string
  processed_at: number
}

type AgentResultsProps = {
  conversationId: number
  sessionId: string
}

export default function AgentResults({ conversationId, sessionId }: AgentResultsProps) {
  const [results, setResults] = useState<AgentResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  console.log(`AgentResults component mounted for conversation ${conversationId}, session ${sessionId}`)

  const fetchResults = async () => {
    try {
      setLoading(true)
      const url = `${VITE_API_BASE_URL}/api/v1/agents/results/${sessionId}:${conversationId}`
      console.log('Fetching agent results from:', url)
      
      const response = await axios.get(url)
      console.log('Agent results response:', response.data)
      
      const newResults = response.data.results || []
      
      // Only update if we have new results
      if (newResults.length !== results.length) {
        console.log('Updating results:', newResults)
        setResults(newResults)
      }
      setError(null)
    } catch (err: any) {
      console.error('Error fetching agent results:', err)
      console.error('Error response:', err.response?.data)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    console.log(`Setting up polling for conversation ${conversationId}, session ${sessionId}`)
    
    // Initial fetch
    fetchResults()
    
    // Set up polling every 2 seconds
    const interval = setInterval(fetchResults, 2000)
    
    return () => {
      console.log(`Cleaning up polling for conversation ${conversationId}, session ${sessionId}`)
      clearInterval(interval)
    }
  }, [conversationId, sessionId])

  if (results.length === 0) {
    return null // Don't show anything if no results
  }

  return (
    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
      <h3 className="text-lg font-semibold mb-3 text-blue-800">🤖 Agent Suggestions</h3>
      {error && (
        <div className="text-red-600 mb-2 p-2 bg-red-50 rounded border border-red-200">
          Error loading results: {error}
        </div>
      )}
      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex justify-between items-start mb-3">
              <span className="font-medium text-blue-700 flex items-center">
                <span className="mr-2">🤖</span>
                {result.agent_type} Agent
              </span>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {result.confidence.toFixed(2)} confidence
              </span>
            </div>
            <div className="text-sm text-gray-700 mb-3 p-2 bg-gray-50 rounded">
              💭 {result.reasoning}
            </div>
            {result.data?.justifications && result.data.justifications.length > 0 && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">
                  💡 Suggested Justifications:
                </div>
                <ul className="space-y-2">
                  {result.data.justifications.map((justification: any, jIndex: number) => (
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
    </div>
  )
} 
