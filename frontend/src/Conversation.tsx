import './App.css'

import {useEffect, useRef, useState} from 'react'
import axios from 'axios'

import type {StepType, ArgMode, ConversationSnapshot, ConversationType} from './types'
import {exportMarkdown} from './markdown'

type UserMode = 'waiting' | 'ready' | 'input'

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500`
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
    argMode: 'thesis',
  }
}

function Conversation({conversation, setConversation, createConversation}: {
  conversation: ConversationType,
  setConversation: (newConversation: ConversationType) => void,
  createConversation: (proposition: string) => void
}) {
  const [histIndex, setHistIndex] = useState<number>(conversation.snapshots.length - 1)
  const lastSnapshot = conversation.snapshots[histIndex]
  const currentSnapshot: ConversationSnapshot = lastSnapshot ?
    lastSnapshot : initialSnapshot()

  const theses = currentSnapshot.theses
  const args = currentSnapshot.args
  const argErrors = currentSnapshot.argErrors
  const [lastPrompt, setLastPrompt] = useState<string>(currentSnapshot.lastPrompt)
  const [userMode, setUserMode] = useState<UserMode>('ready')

  const [prompt, setPrompt] = useState<string>('')
  const [copied, setCopied] = useState<boolean>(false)

  const saveSnapshot = (newSnap: ConversationSnapshot) => {
    setConversation({...conversation, snapshots: [...conversation.snapshots, newSnap]})
    setHistIndex(prev => prev + 1)
  }

  const handleEnter = async (content: string) => {
    if (!content.trim() || userMode == 'waiting') return
    setLastPrompt(content)
    setUserMode('waiting')
    setPrompt('')
    const newUserMode : ArgMode = content == 'Argue.' ? 'development' : currentSnapshot.argMode
    const apiPrompt = newUserMode == 'thesis' ?
      {prompt: content, ...theses} : {prompt: content, ...theses, ...args}
    const path = newUserMode == 'thesis' ? '/api/v1/theses' : '/api/v1/argument'
    const url = VITE_API_BASE_URL + path
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      const newSnapshot = {
        ...conversation.snapshots[histIndex],
        argMode: newUserMode,
        lastPrompt: content,
        theses, args, argErrors,
      }
      if (newUserMode == 'thesis') {
        if (responseObject) {
          const newTheses = responseObject
          saveSnapshot({...newSnapshot, theses: newTheses})
          setLastPrompt('')
        }
        else {
          throw('empty responseObject')
        }
      }
      else {
        if (responseObject && response.data.errors) {
          saveSnapshot({...newSnapshot, args: responseObject,
            argErrors: response.data.errors})
          setLastPrompt('')
        }
        else {
          throw('empty responseObject or missing errors')
        }
      }
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleSupport = async (step_id: string) => {
    const lastPrompt = `Justify proposition (${step_id})`
    setLastPrompt(lastPrompt)
    setUserMode('waiting')
    const apiPrompt = {...args, step_id}
    const url = VITE_API_BASE_URL + '/api/v1/justify'
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)

      if (response.data.errors) {
        throw(response.data.errors)
        return
      }
      if (!responseObject) {
        throw("empty responseObject")
        return
      }

      const newSnapshot = {
        ...conversation.snapshots[histIndex],
        lastPrompt, args: responseObject, argErrors: {},
      }
      saveSnapshot(newSnapshot)
      setLastPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleArgue = async () => {
    handleEnter('Argue.')
  }

  const handleAssume = async (index: string) => {
    handleEnter(`Move proposition (${index}) to the assumptions. Adjust
      inference relations to ensure that every proposition still contributes
      to the argument's conclusion.`)
  }

  const handleRemove = async (index: string) => {
    handleEnter(`Remove proposition (${index}). Adjust
      inference relations to ensure that every proposition still contributes
      to the argument's conclusion.`)
  }

  const handleDispute = async (step: StepType) => {
    createConversation(step.proposition)
  }

  const handleUndo = () => {
    if (histIndex <= 0) return
    const newIndex = histIndex - 1
    setHistIndex(newIndex)
    setUserMode('ready')
  }

  const handleRedo = () => {
    if (histIndex >= conversation.snapshots.length - 1) return
    const newIndex = histIndex + 1
    setHistIndex(newIndex)
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

  const hasLoadedInitPrompt = useRef(false)
  useEffect(() => {
    if (conversation.initPrompt && histIndex == -1 && !hasLoadedInitPrompt.current) {
      hasLoadedInitPrompt.current = true
      handleEnter(conversation.initPrompt)
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

  const argumentNode = (argument: StepType[]) => {
    const argumentSteps = argument.map((step, key) => {
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
        <div key={key}>
          ({step.index}) {step.proposition} [{justifier}; {value}]
          <button
            className={smallButtonClassNames}
            onClick={() => handleSupport(step.index)}>
            support
          </button>
          {key == argument.length -1 ? undefined :
            <>
              <button
                className={smallButtonClassNames}
                onClick={() => handleAssume(step.index)}>
                assume
              </button>
              <button
                className={smallButtonClassNames}
                onClick={() => handleRemove(step.index)}>
                remove
              </button>
              <button
                className={smallButtonClassNames}
                onClick={() => handleDispute(step)}>
                dispute
              </button>
            </>
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
        <div>{argumentNode(args.argument)}</div>
        {!argErrors.argument || argErrors.argument.length == 0 ? undefined :
          <>
            <div className={headingClassNames}>Errors:</div>
            <div>{argErrorsNode(argErrors.argument)}</div>
          </>
        }
      </div>
      <div>
        <div className={headingClassNames}>Counter-Argument:</div>
        <div>{argumentNode(args.counter_argument)}</div>
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
      {args.assumptions.map((assumption, key) => (
        <div key={key}>
          ({assumption.index}) {assumption.proposition}
          <button
            className={smallButtonClassNames}
            onClick={() => handleRemove(assumption.index)}>
            remove
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

  const displayPrompt = lastPrompt || currentSnapshot.lastPrompt
  const lastDiv = (
    <>
      <div className={headingClassNames}>Prompt:</div>
      <div>{displayPrompt}</div>
    </>
  )

  const snapshotId = histIndex == -1 ? '' : `.${histIndex + 1}`

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          <div className={headingClassNames}>Id:</div>
          <div>{conversation.id}{snapshotId}</div>
          {!theses.thesis ? undefined : thesesDiv}
          {args.assumptions.length == 0 ? undefined : assumptionsDiv}
          {args.argument.length == 0 ? undefined : argumentsDiv}
          {!displayPrompt ? undefined : lastDiv}
        </div>
      </div>
      {loadingIndicator}
    </div>
  )

  const placeholderText =
    currentSnapshot.argMode == 'thesis' ? 'Enter thesis' :
    userMode == 'input' ? 'Enter proposition' : ''

  const userDiv = (
    <div className="p-4 flex gap-2 w-[100%] flex-wrap">
      <input
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-none dark:bg-zinc-800"
        value={prompt}
        disabled={!(currentSnapshot.argMode == 'thesis' || userMode == 'input')}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key == 'Enter') {
            handleEnter(prompt)
            e.preventDefault()
          }
        }}
        placeholder={placeholderText}
      />
      {!(currentSnapshot.argMode == 'thesis' || userMode == 'input') ? undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => handleEnter(prompt)}>
          Enter
        </button>
      }
      {!(currentSnapshot.argMode == 'thesis' && theses.thesis) ? undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => handleArgue()}>
          Argue
        </button>
      }
      {!(currentSnapshot.argMode == 'development' && userMode == 'ready') ? undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => setUserMode('input')}>
          Input
        </button>
      }
    </div>
  )

  return (
    <>
      {conversation.snapshots.length < 2 ? undefined :
        <div className="fixed top-4 right-4 z-10 flex gap-2">
          <button
            disabled={histIndex <= 0}
            onClick={handleUndo}
            className={bigButtonClassNames + ' disabled:bg-slate-200 dark:disabled:bg-zinc-800'}>
              Undo
          </button>
          <button
            disabled={histIndex >= conversation.snapshots.length - 1}
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
