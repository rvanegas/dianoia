import './App.css'

import {useEffect, useRef, useState} from 'react'
import axios from 'axios'

import type {StepType, ArgMode, ConversationSnapshot, ConversationType} from './types'
import {exportMarkdown} from './markdown'

type UserMode = 'waiting' | 'ready' | 'input'
type ActionType = 'remove' | 'assume' | 'explain'

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500 disabled:opacity-[25%]`
const headingClassNames = `text-lg font-bold`

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
    vector_store_id: undefined,
  }
}

function Conversation({conversation, setConversation, createConversationFromProposition}: {
  conversation: ConversationType,
  setConversation: (newConversation: ConversationType) => void,
  createConversationFromProposition: (proposition: string) => void
}) {
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

  // input reference 
  const inputRef = useRef<HTMLInputElement>(null)

  const saveSnapshot = (newSnap: ConversationSnapshot, newIndex: boolean = true) => {
    const endShift = newIndex ? 1 : 0
    const truncatedSnapshots = conversation.snapshots.slice(0, snapshotIndex + endShift)
    const newSnapshots = [...truncatedSnapshots, newSnap]
    setSnapshotIndex(prev => prev + endShift)
    setConversation({...conversation, snapshots: newSnapshots})
  }

  // this is just an abbreviation to keep typescript happy
  const argLoc = (loc: string) => {
    return currentSnapshot[loc as keyof typeof currentSnapshot] as any[]
  }

  const handleThesis = async (content?: string) => {
    if (userMode == 'waiting') return
    if (!(content && content.trim()) && !conversation.vector_store_id) return
    content ||= ''
    setPrompt(content)
    setUserMode('waiting')
    setInputText('')
    const apiPrompt = {
      ...currentSnapshot,
      proposition: content,
      vector_store_id: conversation.vector_store_id
    }
    const path = '/api/v1/theses'
    const url = VITE_API_BASE_URL + path
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const argMode : ArgMode = 'thesis'
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        lastPrompt: content,
        argMode,
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleAIJustify = async (loc: string, index: number) =>
  {
    const lastPrompt = `AI Justify proposition ${argLoc(loc)[index].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/ai-justify'
    const apiPrompt = {
      ...currentSnapshot,
      loc, index
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        lastPrompt,
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleArgue = async (thesisAttr: string) => {
    if (!['thesis', 'counter_thesis'].includes(thesisAttr)) {
      throw new Error('bad params')
    }
    const argumentAttr = thesisAttr == 'thesis' ? 'argument' : 'counter_argument'
    const thesisLabel = thesisAttr == 'thesis' ? 'Thesis' : 'Counter-Thesis'
    const lastPrompt = `Argue for ${thesisLabel}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/argue'
    const argMode: ArgMode = 'development'
    let apiPrompt = {
      ...currentSnapshot, 
      loc: argumentAttr, index: 0,
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      // console.log('o', responseObject)
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        argMode,
        lastPrompt
      }
      // console.log('o2', newSnapshot)
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleUserJustify = async (proposition: string) => {
    const lastPrompt = `User Justify proposition ${argLoc(targetLoc)[targetIndex].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/user-justify'
    let apiPrompt = {
      ...currentSnapshot, 
      loc: targetLoc, index: targetIndex,
      proposition
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)

      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        lastPrompt
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const evaluateSteps = async () => {
    const url = VITE_API_BASE_URL + '/api/v1/evaluate'
    try {
      const response = await axios.post(url, currentSnapshot)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        evaluationsPending: false,
      }
      saveSnapshot(newSnapshot, false)
    }
    catch (error) {
      console.error('Error: ', error)
    }
  }

  const handleAction = async (
    action: ActionType, lastPrompt: string, loc: string, index: number
  ) => {
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/' + action
    let apiPrompt = {
      ...currentSnapshot,
      loc, index
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        lastPrompt
      }
      if (action == 'remove' || action == 'assume') {
        newSnapshot.evaluationsPending = true
      }
      else {
        setPrompt(lastPrompt)
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleDispute = async (step: StepType) => {
    createConversationFromProposition(step.proposition)
  }

  const handleUndo = () => {
    if (snapshotIndex <= 0) return
    const newIndex = snapshotIndex - 1
    setSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  const handleRedo = () => {
    if (snapshotIndex >= conversation.snapshots.length - 1) return
    const newIndex = snapshotIndex + 1
    setSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  const handleCopy = async () => {
    const text = exportMarkdown(currentSnapshot)
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  const bottomRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (userMode == 'waiting') {
      bottomRef.current?.scrollIntoView({behavior: 'smooth'})
    }
    
    if (inputRef.current && (userMode == 'ready' || userMode == 'input')) {
      inputRef.current.focus()
    }
  }, [userMode])

  const hasFirstSnapshot = useRef(false)
  const hasCalledTheses = useRef(false)
  useEffect(() => {
    if (snapshotIndex == -1 && !hasFirstSnapshot.current) {
      hasFirstSnapshot.current = true
      saveSnapshot(currentSnapshot)
    }
    if (snapshotIndex == 0 && !hasCalledTheses.current) {
      hasCalledTheses.current = true
      if (conversation.initPrompt || conversation.vector_store_id) {
        handleThesis(conversation.initPrompt)
      }
    }
  }, [snapshotIndex])

  useEffect(() => {
    if (currentSnapshot.evaluationsPending) {
      evaluateSteps()
    }
  }, [currentSnapshot.evaluationsPending])

  const loadingIndicator = userMode != 'waiting' ? undefined : (
    <div className="mt-2 flex items-center space-x-4">
      <span className="text-sm text-zinc-400 italic">
        Dianoia is thinking
      </span>
      <span className="typing-indicator">
        <span className="typing-dot"></span>
        <span className="typing-dot"></span>
        <span className="typing-dot"></span>
      </span>
    </div>
  )

  const argumentNode = (loc: string, argument: StepType[]) => {
    const argumentSteps = argument.map((step, step_index) => {
      let justifier = ''
      let value = `${step.truth}`
      if (step.justifiers.length == 0) {
        justifier = 'premise'
      }
      else {
        justifier = 'from ' + step.justifiers.join(', ')
        value += `, ${step.valid}`
      }
      const valueSpan = 
        <span className={currentSnapshot.evaluationsPending ? 'line-through' : ''}>
          {value}
        </span>
      return (
        <div key={step_index}>
          ({step.symbol}) {step.proposition} [{justifier}; {valueSpan}]
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleAIJustify(loc, step_index)}>
            ai-justify
          </button>
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => {
              setUserMode('input')
              setTargetLoc(loc)
              setTargetIndex(step_index)
            }}>
            user-justify
          </button>
          {step_index == argument.length - 1 || step.justifiers.length != 0 ? undefined :
            <>
              <button
                key="0"
                disabled={userMode == 'waiting'}
                className={smallButtonClassNames}
                onClick={() => {
                  const prompt = `Assume proposition (${step.symbol})`
                  handleAction('assume', prompt, loc, step_index)
                }}>
                assume
              </button>
            </>
          }
          {step_index == argument.length - 1 ? undefined :
            <>
              <button
                key="1"
                disabled={userMode == 'waiting'}
                className={smallButtonClassNames}
                onClick={() => {
                  const prompt = `Remove proposition (${step.symbol})`
                  handleAction('remove', prompt, loc, step_index)
                }}>
                remove
              </button>
              <button
                key="2"
                disabled={userMode == 'waiting'}
                className={smallButtonClassNames}
                onClick={() => handleDispute(step)}>
                dispute
              </button>
            </>
          }
          {step.justifiers.length == 0 ? undefined :
            <button
              key="3"
              disabled={userMode == 'waiting'}
              className={smallButtonClassNames}
              onClick={() => {
                const prompt = `Explain inference to propositon (${step.symbol})`
                handleAction('explain', prompt, loc, step_index)
              }}>
              explain
            </button>
          }
        </div>
      )
    })
    return <div>{argumentSteps}</div>
  }

  const argumentDiv = () => (
    <div>
      <div className={headingClassNames}>Argument:</div>
      <div>{argumentNode('argument', currentSnapshot.argument)}</div>
    </div>
  )

  const counterArgumentDiv = () => (
    <div>
      <div className={headingClassNames}>Counter-Argument:</div>
      <div>{argumentNode('counter_argument', currentSnapshot.counter_argument)}</div>
    </div>
  )

  const assumptionsDiv = (
    <>
      <div className={headingClassNames}>Assumptions:</div>
      {currentSnapshot.assumptions.map((step, step_index) => (
        <div key={step_index}>
          ({step.symbol}) {step.proposition}
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => {
              const prompt = `Remove proposition (${step.symbol})`
              handleAction('remove', prompt, 'assumptions', step_index)
            }}>
            remove
          </button>
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleDispute(step)}>
            dispute
          </button>
        </div>
      ))}
    </>
  )

  const thesesDiv = (
    <>
      <div className={headingClassNames}>Thesis:</div>
      <div>
        {currentSnapshot.thesis}
        {currentSnapshot.argument.length != 0 ? undefined :
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleArgue('thesis')}>
            argue
          </button>
        }
        </div>
      <div className={headingClassNames}>Counter-Thesis:</div>
      <div>
        {currentSnapshot.counter_thesis}
        {currentSnapshot.counter_argument.length != 0 ? undefined :
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleArgue('counter_thesis')}>
            argue
          </button>
        }
      </div>
      <div className={headingClassNames}>Presupposition:</div>
      <div>{currentSnapshot.presupposition}</div>
    </>
  )

  const lastPromptDiv = (
    <>
      <div className={headingClassNames}>LastPrompt:</div>
      <div>{currentSnapshot.lastPrompt}</div>
    </>
  )

  const promptDiv = (
    <>
      <div className={headingClassNames}>Prompt:</div>
      <div>{prompt}</div>
    </>
  )

  const explanationDiv = () => {
    if (!currentSnapshot.formalization || currentSnapshot.formalization.length == 0) return
    return (
      <>
        <div className={headingClassNames}>Formalization:</div>
        <div>{currentSnapshot.formalization.map((prop, key) => (<div key={key}>{prop}</div>))}</div>
        <div className={headingClassNames}>Explanation:</div>
        <div>{currentSnapshot.explanation}</div>
      </>
    )
  }

  const snapshotId = snapshotIndex < 1 ? '' : `.${snapshotIndex}`

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          <div className={headingClassNames}>Id:</div>
          <div>{conversation.id}{snapshotId}</div>
          {!currentSnapshot.thesis ? undefined : thesesDiv}
          {currentSnapshot.assumptions.length == 0 ? undefined : assumptionsDiv}
          {currentSnapshot.argument.length == 0 ? undefined : argumentDiv()}
          {currentSnapshot.counter_argument.length == 0 ? undefined : counterArgumentDiv()}
          {!currentSnapshot.explanation ? undefined : explanationDiv()}
          {!currentSnapshot.lastPrompt ? undefined : lastPromptDiv}
          {!prompt ? undefined : promptDiv}
        </div>
      </div>
      {loadingIndicator}
    </div>
  )

  const placeholderText =
    currentSnapshot.argMode == 'thesis' ? 'Enter thesis' :
    userMode == 'input' ? 'Enter proposition' : ''

  const handleEnter = (prompt: string) => {
    if (currentSnapshot.argMode == 'thesis') {
      handleThesis(prompt)
    }
    else if (userMode == 'input') {
      handleUserJustify(prompt)
    }
    setInputText('')
  }

  const userDiv = (
    <div className="p-4 flex gap-2 w-[100%] flex-wrap">
      <input
        ref={inputRef}
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-2 focus:outline-indigo-500 dark:bg-zinc-800 "
        value={inputText}
        disabled={!(currentSnapshot.argMode == 'thesis' || userMode == 'input')}
        onChange={e => setInputText(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key == 'Enter') {
            handleEnter(inputText)
            e.preventDefault()
          }
        }}
        placeholder={placeholderText}
        tabIndex={1}
      />
      <button
        className={bigButtonClassNames}
        disabled={!(currentSnapshot.argMode == 'thesis' || userMode == 'input')}
        onClick={() => handleEnter(inputText)}
        tabIndex={2}>
        Enter
      </button>
    </div>
  )

  return (
    <>
      {conversation.snapshots.length < 2 ? undefined :
        <div className="fixed top-4 right-4 z-10 flex gap-2">
          <button
            disabled={snapshotIndex <= 0 || userMode == 'waiting'}
            onClick={handleUndo}
            className={bigButtonClassNames + ' disabled:bg-slate-200 dark:disabled:bg-zinc-800'}>
              Undo
          </button>
          <button
            disabled={snapshotIndex >= conversation.snapshots.length - 1
              || userMode == 'waiting'}
            onClick={handleRedo}
            className={bigButtonClassNames + ' disabled:bg-slate-200 dark:disabled:bg-zinc-800'}>
              Redo
          </button>
          <button
            onClick={handleCopy}
            className={bigButtonClassNames}>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      }
      {messagesDiv}
      {userDiv}
    </>
  )
}

export default Conversation
