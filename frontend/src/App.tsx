import './App.css'

import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

import { exportMarkdown } from './markdown.tsx'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

type ThesesType = {
  thesis: string
  counter_thesis: string
  presupposition: string
}

type ArgumentType = {
  index: string
  proposition: string
  justifiers: string[]
  truth: number
}

type ArgsType = {
  argument: ArgumentType
  counter_argument: ArgumentType
}

type UserMode = 'thesis' | 'development' | 'inputProposition' | 'waiting'

// thesis -> waiting -> thesis
// thesis -> waiting -> development
// development -> waiting -> development
// development -> inputProposition -> waiting -> development

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500`
const headingClassNames = `text-lg font-bold`

function ExportButton({textCallback}) {
  const [copied, setCopied] = useState<boolean>(false)
  const handleCopy = async () => {
    await navigator.clipboard.writeText(textCallback())
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }
  return (
    <button
      onClick={handleCopy}
      className={bigButtonClassNames}>
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function App() {
  const [userMode, setUserMode] = useState<UserMode>('thesis')
  const [theses, setTheses] = useState<ThesesType>({
    thesis:'', counter_thesis: '', presupposition: ''})
  const [args, setArgs] = useState<ArgsType>({
    argument: [], counter_argument: []})
  const [lastPrompt, setLastPrompt] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [prompt, setPrompt] = useState<string>('')
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const handleEnter = async (content) => {
    if (!content.trim()) return
    setLastPrompt(content)
    setPrompt('')
    setLoading(true)
    let apiPrompt = {prompt: content, ...theses}
    if (theses.thesis) {
      apiPrompt = {...apiPrompt, ...args}
    }
    const path = theses.thesis ? '/api/v1/argument' : '/api/v1/theses'
    const url = VITE_API_BASE_URL + path
    setUserMode('waiting')
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject.argument) {
        setTheses(responseObject)
        setUserMode('thesis')
      }
      else {
        setArgs(responseObject)
        setUserMode('development')
      }
    } 
    catch (error) {
      console.error('Error: ', error)
      if (theses.argument) {
        setUserMode('development')
      }
      else {
        setUserMode('thesis')
      }
    } 
    finally {
      setLoading(false)
    }
  }

  const handleSupport = async (index, justifiers) => {
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

  const handleRemove = async (index) => {
    handleEnter(`Remove proposition (${index}). Adjust inference
      relations to ensure that every proposition still contributes
      to the argument's conclusion.`)
  }

  const loadingIndicator = loading && (
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
        placeholder={
          userMode == 'thesis' ? 'Enter thesis' :
          userMode == 'inputProposition' ?
            'Enter proposition' : ''
        }
      />
      {userMode == 'development' || userMode == 'waiting' ? 
        undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => handleEnter(prompt)}>
          Enter
        </button>
      }
      {userMode != 'development' ?
        undefined :
        <button
          className={bigButtonClassNames}
          onClick={() => setUserMode('inputProposition')}>
          Input
        </button>
      }
      <ExportButton textCallback={() => exportMarkdown(theses, args)}/>
    </div>
  )

  // console.log('t', theses)
  // console.log('a', args)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({behavior: 'smooth'})
  }, [loading])

  const argumentNode = argument => {
    const argumentSteps = argument.map((step, key) => {
      const justifier = step.justifiers.length == 0 ?
        'premise' : 'from ' + step.justifiers.join(', ')
      return (
        <div key={key}>
          ({step.index}) {step.proposition} [{justifier}; {step.truth}]
          <button
            className={smallButtonClassNames}
            onClick={() => handleSupport(step.index, step.justifiers)}>
            support
          </button>
          {key == argument.length -1 ? undefined :
            <button
              className={smallButtonClassNames}
              onClick={() => handleRemove(step.index)}>
              remove
            </button>
          }
        </div>
      )
    })
    return <div>{argumentSteps}</div>
  }

  const argumentsDiv = (
    <>
      <div>
        <div className={headingClassNames}>Argument:</div>
        <div>{argumentNode(args.argument)}</div>
      </div>
      <div>
        <div className={headingClassNames}>Counter-Argument:</div>
        <div>{argumentNode(args.counter_argument)}</div>
      </div>
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
          {args.argument.length == 0 ? undefined : argumentsDiv}
          {!lastPrompt ? undefined : lastDiv}
        </div>
      </div>
      {loadingIndicator}
    </div>
  )

  const frameDiv = (
    <div className="flex w-[100dvw] h-[100dvh]">
      <div className="flex flex-col items-center w-[250px] bg-slate-200 dark:bg-zinc-800 lg:block hidden">
        <button className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'>
          New Chat
        </button>
      </div>
      <div className="flex flex-1 flex-col h-[100%] w-[100%] bg-white items-center" >
        {messagesDiv}
        {userDiv}
      </div>
    </div>
  )

  return frameDiv
}

export default App
