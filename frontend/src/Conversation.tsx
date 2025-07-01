import './App.css'

import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

import type { ThesesType, StepType, ArgsType, ArgErrors, 
  UserMode, ConversationSnapshot, ConversationType } from './types'
import { exportMarkdown } from './markdown'

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500`
const headingClassNames = `text-lg font-bold`

function Conversation({newConversation}: {
  newConversation: (index: string, proposition: string) => void
}) {
  const [userMode, setUserMode] = useState<UserMode>('thesis')
  const [theses, setTheses] = useState<ThesesType>({
    thesis:'', counter_thesis: '', presupposition: ''})
  const [args, setArgs] = useState<ArgsType>({
    argument: [], counter_argument: [], assumptions: []})
  const [argErrors, setArgErrors] = useState<ArgErrors>({
    argument: [], counter_argument: []})
  const [lastPrompt, setLastPrompt] = useState<string>('')
  const [prompt, setPrompt] = useState<string>('')
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const [conversation, setConversation] = useState<ConversationType>({
    index: 1, name: '', snapshots: []
  })
  const [histIndex, setHistIndex] = useState<number>(0)
  const [copied, setCopied] = useState<boolean>(false)

  const saveSnapshot = (newSnap: ConversationSnapshot) => {
    setConversation({...conversation, snapshots: [...conversation.snapshots, newSnap]})
    setHistIndex(prev => prev + 1)
  }

  const handleEnter = async (content: string) => {
    if (!content.trim() || userMode == 'waiting') return
    setLastPrompt(content)
    setPrompt('')
    const oldUserMode = userMode == 'inputProposition' ? 'development' : userMode
    const newUserMode = content == 'Argue.' ? 'development' : oldUserMode
    let apiPrompt
    if (newUserMode == 'thesis') {
      apiPrompt = {prompt: content, ...theses}
    }
    else {
      apiPrompt = {prompt: content, ...theses, ...args}
    }
    const path = newUserMode == 'development' ? '/api/v1/argument' : '/api/v1/theses'
    const url = VITE_API_BASE_URL + path
    setUserMode('waiting')
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      const newSnapshot = {
        ...conversation.snapshots[histIndex],
        userMode: newUserMode,
        lastPrompt: content,
        theses, args, argErrors,
      }
      if (newUserMode == 'thesis') {
        setTheses(responseObject)
        saveSnapshot({...newSnapshot, theses: responseObject})
      }
      else {
        setArgs(responseObject)
        setArgErrors(response.data.errors)
        saveSnapshot({...newSnapshot, args: responseObject,
          argErrors: response.data.errors})
      }
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode(newUserMode)
    }
  }

  const handleArgue = async () => {
    handleEnter('Argue.')
  }

  const handleSupport = async (index: string, justifiers: string[]) => {
    if (justifiers.length == 0) {
      handleEnter(`Introduce one or two premises from
        which proposition (${index}) is inferred.`
      )
    }
    else {
      handleEnter(`If the inference from which proposition
        (${index}) is inferred is not strictly deductive, introduce
        one or two premises to make the inference more explicit.`
      )
    }
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
    newConversation(step.index, step.proposition)
  }

  const handleUndo = () => {
    if (histIndex <= 0) return
    const newIndex = histIndex - 1
    setHistIndex(newIndex)
    const prev = conversation.snapshots[newIndex]

    setTheses(prev.theses)
    setArgs(prev.args)
    setArgErrors(prev.argErrors)
    setLastPrompt(prev.lastPrompt)
    setUserMode(prev.userMode)
  }

  const handleRedo = () => {
    if (histIndex >= conversation.snapshots.length - 1) return
    const newIndex = histIndex + 1
    setHistIndex(newIndex)
    const next = conversation.snapshots[newIndex]

    setTheses(next.theses)
    setArgs(next.args)
    setArgErrors(next.argErrors)
    setLastPrompt(next.lastPrompt)
    setUserMode(next.userMode)
  }

  const handleCopy = async () => {
    const text = exportMarkdown(theses, args)
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

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

  const placeholderText =
    userMode == 'thesis' ? 'Enter thesis' :
    userMode == 'inputProposition' ?
      'Enter proposition' : ''

  const userDiv = (
    <div className="p-4 flex gap-2 w-[100%] flex-wrap">
      <input
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-none dark:bg-zinc-800"
        value={prompt}
        disabled={userMode == 'development' || userMode == 'waiting'}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key == 'Enter') {
            handleEnter(prompt)
            e.preventDefault()
          }
        }}
        placeholder={placeholderText}
      />
      {userMode == 'development' || userMode == 'waiting' ? undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => handleEnter(prompt)}>
          Enter
        </button>
      }
      {!(userMode == 'thesis' && theses.thesis) ? undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => handleArgue()}>
          Argue
        </button>
      }
      {userMode != 'development' ? undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => setUserMode('inputProposition')}>
          Input
        </button>
      }
      {conversation.snapshots.length < 2 ? undefined :
        <>
          <button
            disabled={histIndex <= 0}
            onClick={handleUndo}
            className={bigButtonClassNames + ' disabled:bg-slate-200'}>
              Undo
          </button>
          <button
            disabled={histIndex >= conversation.snapshots.length - 1}
            onClick={handleRedo}
            className={bigButtonClassNames + ' disabled:bg-slate-200'}>
              Redo
          </button>
        </>
      }
      <button
        onClick={handleCopy}
        className={bigButtonClassNames}>
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  )

  useEffect(() => {
    if (userMode == 'waiting') {
      bottomRef.current?.scrollIntoView({behavior: 'smooth'})
    }
  }, [userMode])

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
            onClick={() => handleSupport(step.index, step.justifiers)}>
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
        {argErrors.argument.length == 0 ? undefined :
          <>
            <div className={headingClassNames}>Errors:</div>
            <div>{argErrorsNode(argErrors.argument)}</div>
          </>
        }
      </div>
      <div>
        <div className={headingClassNames}>Counter-Argument:</div>
        <div>{argumentNode(args.counter_argument)}</div>
        {argErrors.counter_argument.length == 0 ? undefined :
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

  const lastDiv = (
    <>
      <div className={headingClassNames}>Prompt:</div>
      <div>{lastPrompt}</div>
    </>
  )

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          {!theses.thesis ? undefined : thesesDiv}
          {args.assumptions.length == 0 ? undefined : assumptionsDiv}
          {args.argument.length == 0 ? undefined : argumentsDiv}
          {!lastPrompt ? undefined : lastDiv}
        </div>
      </div>
      {loadingIndicator}
    </div>
  )

  return (
    <>
      {messagesDiv}
      {userDiv}
    </>
  )
}

export default Conversation
