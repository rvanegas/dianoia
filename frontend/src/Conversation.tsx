import './App.css'

import {useEffect, useRef, useState} from 'react'
import axios from 'axios'

import type {StepType, ArgsType, ArgMode, ConversationSnapshot, ConversationType} from './types'
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
    theses: {
      thesis: '',
      counter_thesis: '',
      presupposition: '',
    },
    args: {
      assumptions: [],
      argument: [],
      counter_argument: [],
    },
    argErrors: {
      argument: [],
      counter_argument: [],
    },
    lastPrompt: '',
    explanation: '',
    formalization: [],
    argMode: 'thesis',
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

  const theses = currentSnapshot.theses
  const args = currentSnapshot.args
  const argErrors = currentSnapshot.argErrors
  const [prompt, setPrompt] = useState<string>('')

  const [userMode, setUserMode] = useState<UserMode>('ready')
  const [targetLoc, setTargetLoc] = useState<string>('')
  const [targetIndex, setTargetIndex] = useState<number>(0)

  const [inputText, setInputText] = useState<string>('')
  const [copied, setCopied] = useState<boolean>(false)

  const saveSnapshot = (newSnap: ConversationSnapshot) => {
    const truncatedSnapshots = conversation.snapshots.slice(0, snapshotIndex + 1)
    setConversation({...conversation, snapshots: [...truncatedSnapshots, newSnap]})
    setSnapshotIndex(prev => prev + 1)
  }

  // this is just an abbreviation to keep typescript happy
  const argLoc = (loc: string) => {
    return args[loc as keyof typeof args] as any[]
  }

  const handleThesis = async (content?: string) => {
    if (userMode == 'waiting') return
    if (!(content && content.trim()) && !conversation.vector_store_id) return
    content ||= ''
    setPrompt(content)
    setUserMode('waiting')
    setInputText('')
    const apiPrompt = {
      ...theses, ...args, proposition: content,
      vector_store_id: conversation.vector_store_id,
    }
    const path = '/api/v1/theses'
    const url = VITE_API_BASE_URL + path
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw('empty responseObject')
      }
      const argMode : ArgMode = 'thesis'
      const newSnapshot = {
        ...conversation.snapshots[snapshotIndex],
        lastPrompt: content,
        args, argErrors, argMode,
        theses: responseObject,
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

  const handleAIJustifySimple = async (loc: string, index: number) => {
    await handleAIJustify([[loc, index]])
  }

  const handleAIJustify = async (steps: [string, number][], new_args: object = {}) =>
  {
    const lastPrompt = 'Justify propositions'
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/ai-justify'
    let apiPrompt = {
      ...theses, ...args, ...new_args, loc: '', index: 0,
      vector_store_id: conversation.vector_store_id,
    }
    const argMode: ArgMode = 'development'
    let newSnapshot = {
      ...conversation.snapshots[snapshotIndex], argMode,
      lastPrompt, argErrors: initialSnapshot().argErrors,
    }
    let responseObject
    try {
      for (let [loc, index] of steps) {
        apiPrompt.loc = loc
        apiPrompt.index = index
        // console.log('a', apiPrompt)
        const response = await axios.post(url, apiPrompt)
        responseObject = JSON.parse(response.data.reply)

        if (response.data.errors) {
          throw(response.data.errors)
        }
        if (!responseObject) {
          throw('empty responseObject')
        }
        apiPrompt = {...apiPrompt, ...responseObject}
      }
      newSnapshot.args = responseObject
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

  const handleArgue = async () => {
    const new_args: ArgsType = {
      assumptions: [],
      argument: [{
        symbol: 'A',
        proposition: theses.thesis,
        justifiers: [],
        truth: 0.5,
        valid: 0.5,
      }],
      counter_argument: [{
        symbol: 'B',
        proposition: theses.counter_thesis,
        justifiers: [],
        truth: 0.5,
        valid: 0.5,
      }],
    }
    await handleAIJustify([['argument', 0], ['counter_argument', 0]], new_args)
  }

  const handleUserJustify = async (proposition: string) => {
    const lastPrompt = `User Justify proposition ${argLoc(targetLoc)[targetIndex].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/user-justify'
    let apiPrompt = {
      ...theses, ...args, loc: targetLoc, index: targetIndex, proposition,
      vector_store_id: conversation.vector_store_id,
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (response.data.errors) {
        throw(response.data.errors)
      }
      if (!responseObject) {
        throw('empty responseObject')
      }
      const newSnapshot = {
        ...conversation.snapshots[snapshotIndex],
        lastPrompt, argErrors,
        args: responseObject
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

  const handleAction = async (
    action: ActionType, lastPrompt: string, loc: string, index: number
  ) => {
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/' + action
    let apiPrompt = {
      ...theses, ...args, loc, index,
      vector_store_id: conversation.vector_store_id,
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (response.data.errors) {
        throw(response.data.errors)
      }
      if (!responseObject) {
        throw('empty responseObject')
      }
      const newSnapshot = {
        ...conversation.snapshots[snapshotIndex],
        lastPrompt, argErrors: initialSnapshot().argErrors,
        explanation: responseObject.explanation,
        formalization: responseObject.formalization,
        args: responseObject,
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
    const text = exportMarkdown(theses, args)
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  const bottomRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (userMode == 'waiting') {
      bottomRef.current?.scrollIntoView({behavior: 'smooth'})
    }
  }, [userMode])

  const hasLoaded = useRef(false)
  useEffect(() => {
    if (snapshotIndex == -1 && !hasLoaded.current) {
      hasLoaded.current = true
      if (conversation.initPrompt || conversation.vector_store_id) {
        handleThesis(conversation.initPrompt)
      }
    }
  }, [])

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
      return (
        <div key={step_index}>
          ({step.symbol}) {step.proposition} [{justifier}; {value}]
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleAIJustifySimple(loc, step_index)}>
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

  const argErrorsNode = (errors: string[]) => errors.map((error, key) => {
    return (
      <div key={key}>{error}</div>
    )
  })

  const argumentsDiv = (
    <>
      <div>
        <div className={headingClassNames}>Argument:</div>
        <div>{argumentNode('argument', args.argument)}</div>
        {!argErrors.argument || argErrors.argument.length == 0 ? undefined :
          <>
            <div className={headingClassNames}>Errors:</div>
            <div>{argErrorsNode(argErrors.argument)}</div>
          </>
        }
      </div>
      <div>
        <div className={headingClassNames}>Counter-Argument:</div>
        <div>{argumentNode('counter_argument', args.counter_argument)}</div>
        {!argErrors.counter_argument || argErrors.counter_argument.length == 0 ? undefined :
          <>
            <div className={headingClassNames}>Errors:</div>
            <div>{argErrorsNode(argErrors.counter_argument)}</div>
          </>
        }
      </div>
    </>
  )

  const assumptionsDiv = (
    <>
      <div className={headingClassNames}>Assumptions:</div>
      {args.assumptions.map((step, step_index) => (
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
      <div>{theses.thesis}</div>
      <div className={headingClassNames}>Counter-Thesis:</div>
      <div>{theses.counter_thesis}</div>
      <div className={headingClassNames}>Presupposition:</div>
      <div>{theses.presupposition}</div>
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

  const snapshotId = snapshotIndex == -1 ? '' : `.${snapshotIndex + 1}`

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          <div className={headingClassNames}>Id:</div>
          <div>{conversation.id}{snapshotId}</div>
          {!theses.thesis ? undefined : thesesDiv}
          {args.assumptions.length == 0 ? undefined : assumptionsDiv}
          {args.argument.length == 0 ? undefined : argumentsDiv}
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
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-none dark:bg-zinc-800"
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
      />
      <button
        className={bigButtonClassNames}
        disabled={userMode == 'waiting' || userMode == 'ready'}
        onClick={() => handleEnter(inputText)}>
        Enter
      </button>
      {!(currentSnapshot.argMode == 'thesis' && theses.thesis) ? undefined :
        <button
          className={bigButtonClassNames}
          disabled={userMode == 'waiting'}
          onClick={() => handleArgue()}>
          Argue
        </button>
      }
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
