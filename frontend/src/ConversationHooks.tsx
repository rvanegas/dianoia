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
    assumptions: [],
    argument: [],
    // evaluationsPending: false, // DISABLED: Old evaluation system
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



  // export button
  const [copied, setCopied] = useState<boolean>(false)

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
    copied,
    setCopied,
    inputRef,
    saveSnapshot,
    sessionId
  }
}

export function useConversationActions(
  currentSnapshot: ConversationSnapshot,
  userMode: UserMode,
  setUserMode: (mode: UserMode) => void,

  setInputText: (text: string) => void,
  targetLoc: string,
  targetIndex: number,
  saveSnapshot: (newSnap: ConversationSnapshot, inPlace?: boolean, convName?: string) => void,
  createConversationFromProposition: (proposition: string) => void,
  conversationId: number,
  sessionId: string,
  snapshotIndex: number
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
      // Add conversation_id as query parameter (format: session_id:conversation_id)
      const url = new URL(operationInfo.url)
      url.searchParams.set('conversation_id', `${sessionId}:${conversationId}`)
      url.searchParams.set('snapshot_id', String(snapshotIndex + 1))
      
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

    setInputText('')
    
    let apiPrompt = {
      ...currentSnapshot,
      proposition: content,
    }
    let url = VITE_API_BASE_URL + '/api/argument/argue'
    let newSnapshot = currentSnapshot
    const argMode: ArgMode = 'development'
    
    // First API call to create thesis
    const thesisResponseObject = await makeApiCall(
      {
        url, data: apiPrompt, onSuccess: (responseObject) => {
          newSnapshot = {
            ...currentSnapshot,
            ...responseObject,
            argMode,
          }
          saveSnapshot(newSnapshot)
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
            argMode,
          }
          saveSnapshot(finalSnapshot, false, responseObject.name)
        }, onFinally: () => {}, operationName: 'Generate Name'
      }
    )
  }

  // DISABLED: Old AI Justify handler - replaced by new agent system
  // const handleAIJustify = async (loc: string, index: number) => {
  //   setUserMode('waiting')
  //   
  //   const url = VITE_API_BASE_URL + '/api/argument/ai-justify'
  //   const apiPrompt = {
  //     ...currentSnapshot,
  //     loc, index
  //   }
  //   
  //   await makeApiCall(
  //     { url, data: apiPrompt, onSuccess: (responseObject) => {
  //       const newSnapshot = {
  //         ...currentSnapshot,
  //         ...responseObject,
  //         evaluationsPending: true,
  //       }
  //       saveSnapshot(newSnapshot)
  //     }, onFinally: () => setUserMode('ready'), operationName: 'AI Justify' }
  //   )
  // }



  const handleUserJustify = async (proposition: string) => {
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
          // evaluationsPending: true, // DISABLED: Old evaluation system
        }
        saveSnapshot(newSnapshot)
      }, onFinally: () => setUserMode('ready'), operationName: 'User Justify' }
    )
  }

  // DISABLED: Old evaluate steps function - replaced by new agent system
  // verify that user hasn't moved away and potentially replaced 
  // contents of this snapshot. saveSnapshot() is then called 
  // with inPlace = true
  // const evaluateSteps = async (snapshotRenderCount: React.MutableRefObject<number>) => {
  //   const url = VITE_API_BASE_URL + '/api/argument/evaluate'
  //   
  //   try {
  //     setEvaluatingMode(true)
  //     const currentSnapshotRenderCount = snapshotRenderCount.current
  //     
  //     await makeApiCall({
  //       url,
  //       data: currentSnapshot,
  //       onSuccess: (responseObject) => {
  //         if (currentSnapshotRenderCount != snapshotRenderCount.current) return
  //         if (!responseObject) {
  //           throw new Error('empty responseObject')
  //         }
  //         const newSnapshot = {
  //           ...currentSnapshot,
  //           ...responseObject,
  //           evaluationsPending: false,
  //         }
  //         saveSnapshot(newSnapshot, true)
  //       },
  //       onFinally: () => setEvaluatingMode(false),
  //       operationName: 'Evaluate'
  //     })
  //   } catch (error: any) {
  //     // Error handling is already done in makeApiCall
  //     setEvaluatingMode(false)
  //   }
  // }

  const handleAction = async (
    action: ActionType, loc: string, index: number, errorLabel: string
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
        }
        // DISABLED: Old evaluation system
        // if (action == 'remove' || action == 'assume') {
        //   newSnapshot.evaluationsPending = true
        // }
        saveSnapshot(newSnapshot)
      }, onFinally: () => setUserMode('ready'), operationName: errorLabel }
    )
  }

  const handleDispute = async (step: StepType) => {
    createConversationFromProposition(step.proposition)
  }

  return {
    handleThesis,
    // handleAIJustify, // DISABLED: Old AI Justify handler - replaced by new agent system
    handleUserJustify,
    // evaluateSteps, // DISABLED: Old evaluate steps function - replaced by new agent system
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
  snapshotRenderCount: React.RefObject<number>
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
