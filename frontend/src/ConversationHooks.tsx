import {useState, useRef} from 'react'
import axios from 'axios'

import type {StepType, ArgMode, ConversationSnapshot, ConversationType} from './types'

type UserMode = 'waiting' | 'ready' | 'input'
type ActionType = 'remove' | 'assume' | 'explain'

// Type for API operation information
type ApiOperationInfo = {
  url: string;
  data: any;
  onSuccess: (responseObject: any) => void;
  onFinally?: () => void;
  operationName: string;
}

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

// Generate session UUID once per browser session (module-level)
let sessionId: string | null = null

function getSessionId(): string {
  if (!sessionId) {
    sessionId = crypto.randomUUID()
  }
  return sessionId
}

function initialSnapshot() : ConversationSnapshot {
  return {
    thesis: '',
    assumptions: [],
    argument: [],
    lastPrompt: '',
    evaluationsPending: false,
    explanation: '',
    argMode: 'thesis',
    file_ids: []
  }
}

export function useConversationState(
  conversation: ConversationType,
  setConversation: (newConversation: ConversationType) => void
) {
  // Get the session UUID (generated once per browser session)
  const sessionId = getSessionId()

  const snapshotRenderCount = useRef(0)
  const [snapshotIndex, setSnapshotIndex] = useState<number>(conversation.snapshots.length - 1)
  const lastSnapshot = conversation.snapshots[snapshotIndex]
  const currentSnapshot: ConversationSnapshot = lastSnapshot ?
    lastSnapshot : initialSnapshot()

  // ready/waiting/input
  const [userMode, setUserMode] = useState<UserMode>('ready')

  // used by input to save which user-justify action was selected
  const [targetLoc, setTargetLoc] = useState<string>('')
  const [targetIndex, setTargetIndex] = useState<number>(0)

  // contents of input element
  const [inputText, setInputText] = useState<string>('')

  // should rename to currentPrompt. this is prompt backend is currently working on.
  const [prompt, setPrompt] = useState<string>('')

  // export button
  const [copied, setCopied] = useState<boolean>(false)

  // evaluating mode for score evaluation
  const [evaluatingMode, setEvaluatingMode] = useState<boolean>(false)

  // input reference 
  const inputRef = useRef<HTMLInputElement>(null)

  // this saves new versions of argument. if inplace is true, then only annotations
  // should change
  const saveSnapshot = (newSnap: ConversationSnapshot, inPlace: boolean = false, convName: string = '') => {
    const oldSnaps = conversation.snapshots
    let newSnaps
    if (inPlace) {
      newSnaps = [...oldSnaps.slice(0, snapshotIndex), newSnap,
        ...oldSnaps.slice(snapshotIndex + 1)]
    }
    else {
      newSnaps = [...oldSnaps.slice(0, snapshotIndex + 1), newSnap]
      snapshotRenderCount.current += 1
      const newSnapshotIndex = snapshotIndex + 1
      setSnapshotIndex(newSnapshotIndex)
    }
    const newConversation = {...conversation, snapshots: newSnaps}
    if (convName) newConversation.name = convName
    setConversation(newConversation)
  }

  // this is just an abbreviation to keep typescript happy
  const argLoc = (loc: string) => {
    return currentSnapshot[loc as keyof typeof currentSnapshot] as any[]
  }

  return {
    snapshotRenderCount,
    snapshotIndex,
    setSnapshotIndex,
    currentSnapshot,
    userMode,
    setUserMode,
    targetLoc,
    setTargetLoc,
    targetIndex,
    setTargetIndex,
    inputText,
    setInputText,
    prompt,
    setPrompt,
    copied,
    setCopied,
    evaluatingMode,
    setEvaluatingMode,
    inputRef,
    saveSnapshot,
    argLoc,
    sessionId
  }
}

export function useConversationActions(
  currentSnapshot: ConversationSnapshot,
  userMode: UserMode,
  setUserMode: (mode: UserMode) => void,
  setPrompt: (prompt: string) => void,
  setInputText: (text: string) => void,
  targetLoc: string,
  targetIndex: number,
  argLoc: (loc: string) => any[],
  saveSnapshot: (newSnap: ConversationSnapshot, inPlace?: boolean, convName?: string) => void,
  createConversationFromProposition: (proposition: string) => void,
  setEvaluatingMode: (mode: boolean) => void,
  conversationId: number,
  sessionId: string
) {
  // State for tracking retry information
  const [lastFailedOperation, setLastFailedOperation] = useState<ApiOperationInfo | null>(null);

  // Reusable error handler
  const handleApiError = (error: any, operationInfo?: ApiOperationInfo) => {
    // Handle HTTP errors (like 422 AssistantResponseError)
    if (error.response?.status === 422 && error.response?.data?.detail) {
      console.log('AssistantResponseError detected:', error.response.data.detail)
      if (operationInfo) {
        setLastFailedOperation(operationInfo)
      }
    }
    // Handle other types of errors (JSON parsing, network, etc.)
    else if (operationInfo) {
      console.log('API Error detected:', error.message)
      setLastFailedOperation(operationInfo)
    }
    
    console.error('Error: ', error)
  }

  // Reusable API call wrapper
  const makeApiCall = async (operationInfo: ApiOperationInfo) => {
    try {
      // Add session_id and conversation_id as query parameters
      const url = new URL(operationInfo.url)
      url.searchParams.set('session_id', sessionId)
      url.searchParams.set('conversation_id', conversationId.toString())
      
      const response = await axios.post(url.toString(), operationInfo.data)
      
      // Check if response data exists
      if (!response.data || !response.data.reply) {
        throw new Error('Invalid response format: missing reply data')
      }
      
      // Parse JSON response
      let responseObject
      try {
        responseObject = JSON.parse(response.data.reply)
      } catch (parseError) {
        throw new Error(`Invalid JSON response: ${parseError instanceof Error ? parseError.message : 'Unknown parsing error'}`)
      }
      
      // Check if parsed object is valid
      if (!responseObject) {
        throw new Error('Empty response object')
      }
      
      operationInfo.onSuccess(responseObject)
      // Clear any previous failed operation on success
      setLastFailedOperation(null)
      return responseObject
    } catch (error: any) {
      handleApiError(error, operationInfo)
    } finally {
      operationInfo.onFinally?.()
    }
  }

  // Retry function
  const retryLastOperation = async () => {
    if (!lastFailedOperation) return
    
    setUserMode('waiting')
    await makeApiCall(lastFailedOperation)
  }

  const handleThesis = async (content?: string) => {
    if (userMode == 'waiting') return
    if (!(content && content.trim())) return
    setPrompt(content)
    setInputText('')
    
    let apiPrompt = {
      ...currentSnapshot,
      proposition: content,
    }
    let url = VITE_API_BASE_URL + '/api/argument/argue'
    let newSnapshot = currentSnapshot
    const argMode: ArgMode = 'thesis'
    
    // First API call to create thesis
    const thesisResponseObject = await makeApiCall(
      {
        url, data: apiPrompt, onSuccess: (responseObject) => {
          newSnapshot = {
            ...currentSnapshot,
            ...responseObject,
            lastPrompt: content,
            argMode,
          }
          saveSnapshot(newSnapshot)
          setPrompt('')
        }, onFinally: () => setUserMode('ready'), operationName: 'Create Thesis'
      }
    )

    url = VITE_API_BASE_URL + '/api/argument/gen-name'
    apiPrompt = {
      ...currentSnapshot,
      ...thesisResponseObject,
      proposition: content,
    }

    await makeApiCall(
      {
        url, data: apiPrompt, onSuccess: (responseObject) => {
          const finalSnapshot = {
            ...currentSnapshot,
            ...thesisResponseObject,
            lastPrompt: content,
            argMode,
          }
          saveSnapshot(finalSnapshot, false, responseObject.name)
          setPrompt('')
        }, onFinally: () => {}, operationName: 'Generate Name'
      }
    )
  }

  const handleAIJustify = async (loc: string, index: number) => {
    const lastPrompt = `AI Justify proposition ${argLoc(loc)[index].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/argument/ai-justify'
    const apiPrompt = {
      ...currentSnapshot,
      loc, index
    }
    
    await makeApiCall(
      { url, data: apiPrompt, onSuccess: (responseObject) => {
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          evaluationsPending: true,
          lastPrompt,
        }
        saveSnapshot(newSnapshot)
        setPrompt('')
      }, onFinally: () => setUserMode('ready'), operationName: 'AI Justify' }
    )
  }

  const handleArgue = async (thesisAttr: string) => {
    if (thesisAttr !== 'thesis') {
      throw new Error('bad params')
    }
    const argumentAttr = 'argument'
    const thesisLabel = 'Thesis'
    const lastPrompt = `Argue for ${thesisLabel}`
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/argument/argue'
    const argMode: ArgMode = 'development'
    const apiPrompt = {
      ...currentSnapshot, 
      loc: argumentAttr, index: 0,
    }
    
    await makeApiCall(
      { url, data: apiPrompt, onSuccess: (responseObject) => {
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          argMode,
          lastPrompt
        }
        saveSnapshot(newSnapshot)
        setPrompt('')
      }, onFinally: () => setUserMode('ready'), operationName: 'Argue' }
    )
  }

  const handleUserJustify = async (proposition: string) => {
    const lastPrompt = `User Justify proposition ${argLoc(targetLoc)[targetIndex].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/argument/user-justify'
    const apiPrompt = {
      ...currentSnapshot, 
      loc: targetLoc, index: targetIndex,
      proposition
    }
    
    await makeApiCall(
      { url, data: apiPrompt, onSuccess: (responseObject) => {
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          evaluationsPending: true,
          lastPrompt
        }
        saveSnapshot(newSnapshot)
        setPrompt('')
      }, onFinally: () => setUserMode('ready'), operationName: 'User Justify' }
    )
  }

  // verify that user hasn't moved away and potentially replaced 
  // contents of this snapshot. saveSnapshot() is then called 
  // with inPlace = true
  const evaluateSteps = async (snapshotRenderCount: React.MutableRefObject<number>) => {
    const url = VITE_API_BASE_URL + '/api/argument/evaluate'
    
    try {
      setEvaluatingMode(true)
      const currentSnapshotRenderCount = snapshotRenderCount.current
      
      await makeApiCall({
        url,
        data: currentSnapshot,
        onSuccess: (responseObject) => {
          if (currentSnapshotRenderCount != snapshotRenderCount.current) return
          if (!responseObject) {
            throw new Error('empty responseObject')
          }
          const newSnapshot = {
            ...currentSnapshot,
            ...responseObject,
            evaluationsPending: false,
          }
          saveSnapshot(newSnapshot, true)
        },
        onFinally: () => setEvaluatingMode(false),
        operationName: 'Evaluate'
      })
    } catch (error: any) {
      // Error handling is already done in makeApiCall
      setEvaluatingMode(false)
    }
  }

  const handleAction = async (
    action: ActionType, lastPrompt: string, loc: string, index: number, errorLabel: string
  ) => {
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/argument/' + action
    const apiPrompt = {
      ...currentSnapshot,
      loc, index
    }
    
    await makeApiCall(
      { url, data: apiPrompt, onSuccess: (responseObject) => {
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          lastPrompt
        }
        if (action == 'remove' || action == 'assume') {
          newSnapshot.evaluationsPending = true
        } else {
          setPrompt(lastPrompt)
        }
        saveSnapshot(newSnapshot)
        setPrompt('')
      }, onFinally: () => setUserMode('ready'), operationName: errorLabel }
    )
  }

  const handleDispute = async (step: StepType) => {
    createConversationFromProposition(step.proposition)
  }

  return {
    handleThesis,
    handleAIJustify,
    handleArgue,
    handleUserJustify,
    evaluateSteps,
    handleAction,
    handleDispute,
    retryLastOperation,
    lastFailedOperation
  }
}

export function useConversationNavigation(
  snapshotIndex: number,
  conversation: ConversationType,
  setSnapshotIndex: (index: number) => void,
  setUserMode: (mode: UserMode) => void,
  snapshotRenderCount: React.MutableRefObject<number>
) {
  const handleUndo = () => {
    if (snapshotIndex <= 0) return
    const newIndex = snapshotIndex - 1
    snapshotRenderCount.current += 1
    setSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  const handleRedo = () => {
    if (snapshotIndex >= conversation.snapshots.length - 1) return
    const newIndex = snapshotIndex + 1
    snapshotRenderCount.current += 1
    setSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  return {
    handleUndo,
    handleRedo
  }
}
