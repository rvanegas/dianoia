import {useRef, useState} from 'react'
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

function initialSnapshot() : ConversationSnapshot {
  return {
    thesis: '',
    counter_thesis: '',
    presupposition: '',
    assumptions: [],
    argument: [],
    counter_argument: [],
    lastPrompt: '',
    evaluationsPending: false,
    explanation: '',
    formalization: [],
    argMode: 'thesis',
    file_ids: [],
  }
}

export function useConversationState(
  conversation: ConversationType,
  setConversation: (newConversation: ConversationType) => void
) {
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
      setSnapshotIndex(prev => prev + 1)
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
    argLoc
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
  setEvaluatingMode: (mode: boolean) => void
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
      const response = await axios.post(operationInfo.url, operationInfo.data)
      
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
    setUserMode('waiting')
    setInputText('')
    
    const apiPrompt = {
      ...currentSnapshot,
      proposition: content,
    }
    const url = VITE_API_BASE_URL + '/api/v1/theses'
    
    await makeApiCall(
      { url, data: apiPrompt, onSuccess: (responseObject) => {
        const argMode: ArgMode = 'thesis'
        const newSnapshot = {
          ...currentSnapshot,
          ...responseObject,
          lastPrompt: content,
          argMode,
        }
        saveSnapshot(newSnapshot, false, responseObject.name)
        setPrompt('')
      }, onFinally: () => setUserMode('ready'), operationName: 'Create Thesis' }
    )
  }

  const handleAIJustify = async (loc: string, index: number) => {
    const lastPrompt = `AI Justify proposition ${argLoc(loc)[index].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/v1/ai-justify'
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
    if (!['thesis', 'counter_thesis'].includes(thesisAttr)) {
      throw new Error('bad params')
    }
    const argumentAttr = thesisAttr == 'thesis' ? 'argument' : 'counter_argument'
    const thesisLabel = thesisAttr == 'thesis' ? 'Thesis' : 'Counter-Thesis'
    const lastPrompt = `Argue for ${thesisLabel}`
    setUserMode('waiting')
    
    const url = VITE_API_BASE_URL + '/api/v1/argue'
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
    
    const url = VITE_API_BASE_URL + '/api/v1/user-justify'
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
    const url = VITE_API_BASE_URL + '/api/v1/evaluate'
    
    try {
      setEvaluatingMode(true)
      const currentSnapshotRenderCount = snapshotRenderCount.current
      const response = await axios.post(url, currentSnapshot)
      if (currentSnapshotRenderCount != snapshotRenderCount.current) return
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        evaluationsPending: false,
      }
      saveSnapshot(newSnapshot, true)
      // Clear any previous failed operation on success
      setLastFailedOperation(null)
    } catch (error: any) {
      handleApiError(error, {
        url,
        data: currentSnapshot,
        onSuccess: (responseObject) => {
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
    } finally {
      setEvaluatingMode(false)
    }
  }

  const handleAction = async (
    action: ActionType, lastPrompt: string, loc: string, index: number, errorLabel: string
  ) => {
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/' + action
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
