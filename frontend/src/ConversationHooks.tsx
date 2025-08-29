import {useState, useRef} from 'react'
import axios from 'axios'

import type {StepType, ArgMode, ConversationSnapshot, ConversationType} from './types'
import { useConversationStore, initialSnapshot } from './conversationStore'

type UserMode = 'waiting' | 'ready' | 'input'
type ActionType = 'remove' | 'assume' | 'explain' | 'endorse-formalization'

// Type for API operation information
type ApiOperationInfo = {
  url: string;
  data: any;
  onSuccess: (responseObject: any, getCurrentConversationState: () => { conversation: ConversationType, snapshotIndex: number }) => void;
  onFinally?: () => void;
  operationName: string;
}

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL



export function useConversationState(
  conversation: ConversationType,
  setConversation: (newConversation: ConversationType) => void
) {
  // Get the session UUID, userMode, currentSnapshotIndex, and snapshotRenderCount from the store
  const { sessionId, userMode, setUserMode, currentSnapshotIndex, setCurrentSnapshotIndex, 
    snapshotRenderCount, setSnapshotRenderCount } = useConversationStore()

  const lastSnapshot = conversation.snapshots[currentSnapshotIndex]
  const currentSnapshot: ConversationSnapshot = lastSnapshot ?
    lastSnapshot : initialSnapshot()

  // used by input to save which user-justify action was selected
  const [targetLoc, setTargetLoc] = useState<string>('')
  const [targetIndex, setTargetIndex] = useState<number>(0)

  // contents of input element
  const [inputText, setInputText] = useState<string>('')



  // export button
  const [copied, setCopied] = useState<boolean>(false)

  // input reference 
  const inputRef = useRef<HTMLInputElement>(null)

  // this saves new versions of argument
  const saveSnapshot = (newSnap: ConversationSnapshot, convName: string = '') => {
    const oldSnaps = conversation.snapshots
    const newSnaps = [...oldSnaps.slice(0, currentSnapshotIndex + 1), newSnap]
    setSnapshotRenderCount(snapshotRenderCount + 1)
    const newSnapshotIndex = currentSnapshotIndex + 1
    setCurrentSnapshotIndex(newSnapshotIndex)
    const newConversation = {...conversation, snapshots: newSnaps}
    if (convName) newConversation.name = convName
    setConversation(newConversation)
  }

  const saveSnapshotInPlace = (newSnap: ConversationSnapshot) => {
    const oldSnaps = conversation.snapshots
    let newSnaps
    newSnaps = [...oldSnaps.slice(0, currentSnapshotIndex), newSnap,
      ...oldSnaps.slice(currentSnapshotIndex + 1)]
    const newConversation = {...conversation, snapshots: newSnaps}
    setConversation(newConversation)
  }

  return {
    snapshotRenderCount,
    snapshotIndex: currentSnapshotIndex,
    setSnapshotIndex: setCurrentSnapshotIndex,
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
    saveSnapshotInPlace,
    sessionId
  }
}

export function useConversationActions(
  currentSnapshot: ConversationSnapshot,
  setInputText: (text: string) => void,
  targetLoc: string,
  targetIndex: number,
  saveSnapshot: (newSnap: ConversationSnapshot, convName?: string) => void,
  saveSnapshotInPlace: (newSnap: ConversationSnapshot) => void,
  createConversationFromProposition: (proposition: string) => void,
  conversationId: number,
  conversation: ConversationType
) {
  // State for tracking retry information
  const [lastFailedOperation, setLastFailedOperation] = useState<ApiOperationInfo | null>(null);
  const { saveConversationName, sessionId, userMode, setUserMode, currentSnapshotIndex } = useConversationStore()

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
  const makeApiCall = async (operationInfo: ApiOperationInfo, conversation: ConversationType) => {
    try {
      // Add conversation_id as query parameter (format: session_id:conversation_id)
      const url = new URL(operationInfo.url)
      url.searchParams.set('conversation_id', `${sessionId}:${conversationId}`)
      url.searchParams.set('snapshot_id', String(currentSnapshotIndex + 1))
      
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
      
      // Create a getter function that returns the current conversation state
      const getCurrentConversationState = () => {
        return { conversation, snapshotIndex: currentSnapshotIndex }
      }
      
      operationInfo.onSuccess(responseObject, getCurrentConversationState)
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
    await makeApiCall(lastFailedOperation, conversation)
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
    const argMode: ArgMode = 'development'
    
    // First API call to create thesis
    const thesisResponseObject = await makeApiCall(
      {
        url, data: apiPrompt, onSuccess: (responseObject, getCurrentConversationState) => {
        const { conversation, snapshotIndex } = getCurrentConversationState()
        const currentSnapshot = conversation.snapshots[snapshotIndex] || initialSnapshot()
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          argMode,
        }
        saveSnapshot(newSnapshot)
        }, onFinally: () => setUserMode('ready'), operationName: 'Create Thesis'
      }, conversation
    )

    url = VITE_API_BASE_URL + '/api/argument/gen-name'
    apiPrompt = {
      ...currentSnapshot,
      ...thesisResponseObject,
      proposition: content,
    }

    await makeApiCall(
      {
        url, data: apiPrompt, onSuccess: (responseObject, getCurrentConversationState) => {
          const { conversation, snapshotIndex } = getCurrentConversationState()
          const currentSnapshot = conversation.snapshots[snapshotIndex] || initialSnapshot()
          const finalSnapshot = {
            ...currentSnapshot,
            ...thesisResponseObject,
            argMode,
          }
          saveSnapshot(finalSnapshot)
          saveConversationName(conversation.id, responseObject.name)
        }, onFinally: () => {}, operationName: 'Generate Name'
      }, conversation
    )
  }

  const handleUserJustify = async (proposition: string) => {
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/argument/user-justify'
    const apiPrompt = {
      ...currentSnapshot, 
      loc: targetLoc, index: targetIndex,
      proposition
    }
    
    await makeApiCall(
      { url, data: apiPrompt, onSuccess: (responseObject, getCurrentConversationState) => {
        const { conversation, snapshotIndex } = getCurrentConversationState()
        const currentSnapshot = conversation.snapshots[snapshotIndex] || initialSnapshot()
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          // evaluationsPending: true, // DISABLED: Old evaluation system
        }
        saveSnapshot(newSnapshot)
      }, onFinally: () => setUserMode('ready'), operationName: 'User Justify' },
      conversation
    )
  }

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
      { url, data: apiPrompt, onSuccess: (responseObject, getCurrentConversationState) => {
        const { conversation, snapshotIndex } = getCurrentConversationState()
        const currentSnapshot = conversation.snapshots[snapshotIndex] || initialSnapshot()
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
        }
        // DISABLED: Old evaluation system
        // if (action == 'remove' || action == 'assume') {
        //   newSnapshot.evaluationsPending = true
        // }
        saveSnapshot(newSnapshot)
      }, onFinally: () => setUserMode('ready'), operationName: errorLabel },
      conversation
    )
  }

  const handleEndorseFormalization = async (
    loc: string, index: number, endorsed: boolean
  ) => {
    // Update endorsement status locally in the snapshot
    const newSnapshot = { ...currentSnapshot }
    
    if (loc === 'argument' && newSnapshot.argument[index]?.formalization) {
      // Create new array and formalization object to avoid read-only property error
      newSnapshot.argument = [...newSnapshot.argument]
      newSnapshot.argument[index] = {
        ...newSnapshot.argument[index],
        formalization: {
          ascii: newSnapshot.argument[index].formalization!.ascii,
          json_structure: newSnapshot.argument[index].formalization!.json_structure,
          endorsed: endorsed
        }
      }
    } else if (loc === 'assumptions' && newSnapshot.assumptions[index]?.formalization) {
      // Create new array and formalization object to avoid read-only property error
      newSnapshot.assumptions = [...newSnapshot.assumptions]
      newSnapshot.assumptions[index] = {
        ...newSnapshot.assumptions[index],
        formalization: {
          ascii: newSnapshot.assumptions[index].formalization!.ascii,
          json_structure: newSnapshot.assumptions[index].formalization!.json_structure,
          endorsed: endorsed
        }
      }
    }
    
    saveSnapshotInPlace(newSnapshot)
  }

  const handleRejectFormalization = async (
    loc: string, index: number
  ) => {
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/argument/reject-formalization'
    // Omit formalization_definitions to avoid biasing the formalizer
    const { formalization_definitions, ...snapshotWithoutDefinitions } = currentSnapshot
    const apiPrompt = {
      ...snapshotWithoutDefinitions,
      loc, index
    }
    
    await makeApiCall(
      { 
        url, 
        data: apiPrompt, 
        onSuccess: (responseObject, getCurrentConversationState) => {
          const { conversation, snapshotIndex } = getCurrentConversationState()
          const currentSnapshot = conversation.snapshots[snapshotIndex] || initialSnapshot()
          const newSnapshot = {
            ...currentSnapshot,
            ...responseObject,
          }
          saveSnapshot(newSnapshot)
        }, 
        onFinally: () => setUserMode('ready'), 
        operationName: 'Reject formalization' 
      },
      conversation
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
    handleEndorseFormalization,
    handleRejectFormalization,
    handleDispute,
    retryLastOperation,
    lastFailedOperation
  }
}

export function useConversationNavigation(
  conversation: ConversationType,
  setUserMode: (mode: UserMode) => void
) {
  const { snapshotRenderCount, setSnapshotRenderCount, currentSnapshotIndex, setCurrentSnapshotIndex } = useConversationStore()

  const handleUndo = () => {
    if (currentSnapshotIndex <= 0) return
    const newIndex = currentSnapshotIndex - 1
    setSnapshotRenderCount(snapshotRenderCount + 1)
    setCurrentSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  const handleRedo = () => {
    if (currentSnapshotIndex >= conversation.snapshots.length - 1) return
    const newIndex = currentSnapshotIndex + 1
    setSnapshotRenderCount(snapshotRenderCount + 1)
    setCurrentSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  return {
    handleUndo,
    handleRedo
  }
}
