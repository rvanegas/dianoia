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

type UserMode = 'thesis' | 'development' | 'inputProposition'

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
  const [prompt, setPrompt] = useState<string>('')
  const [userMode, setUserMode] = useState<UserMode>('thesis')
  const [lastPrompt, setLastPrompt] = useState<string>('')
  const [theses, setTheses] = useState<ThesesType>({thesis:'', counter_thesis: '', presupposition: ''})
  const [args, setArgs] = useState({argument: [], counter_argument: []})
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const handleSend = async (content) => {
    if (theses.thesis != '') {
      handleArgsSend(content)
      return
    }
    if (!content.trim()) return
    setLastPrompt(content)
    setPrompt('')
    setLoading(true)
    const thesesPrompt = {prompt: content, ...theses}
    try {
      const url = `${VITE_API_BASE_URL}/api/v1/theses`
      const response = await axios.post(url, thesesPrompt)
      setTheses(JSON.parse(response.data.reply))
    } catch (error) {
      console.error('Error: ', error)
    } finally {
      setLoading(false)
    }
  }

  const handleArgsSend = async (content) => {
    if (!content.trim()) return
    setLastPrompt(content)
    setPrompt('')
    setLoading(true)
    const argumentPrompt = {prompt: content, ...theses, ...args}
    try {
      const url = `${VITE_API_BASE_URL}/api/v1/argument`
      const response = await axios.post(url, argumentPrompt)
      setArgs(JSON.parse(response.data.reply))
    } catch (error) {
      console.error('Error: ', error)
    } finally {
      setLoading(false)
      setUserMode('development')
    }
  }

  const handleExpandPremise = async (index) => {
    handleSend(`Introduce one or two premises from
      which proposition (${index}) is inferred.`
    )
  }

  const handleExpandInference = async (index) => {
    handleSend(`If the inference from which proposition
      (${index}) is inferred is not strictly deductive, introduce
      one or two premises to make the inference more explicit.`
    )
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({behavior: 'smooth'})
  }, [messages, loading])

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

  // window.xmessages = messages

  const placeholderText =
    userMode == 'thesis' ? 'Enter thesis' :
    userMode == 'inputProposition' ?
      'Enter proposition' : ''

  const userDiv = (
    <div className="p-4 flex gap-2 w-[100%] flex-wrap">
      <input
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-none dark:bg-zinc-800"
        value={prompt}
        disabled={userMode == 'development'}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key == "Enter") {
            handleSend(prompt)
            e.preventDefault()
          }
        }}
        placeholder={
          userMode == 'thesis' ? 'Enter thesis' :
          userMode == 'inputProposition' ?
            'Enter proposition' : ''
        }
      />
      <button
        onClick={() => handleSend(prompt)}
        className={bigButtonClassNames}>
        Enter
      </button>
      <ExportButton textCallback={() => exportMarkdown(theses, args)}/>
    </div>
  )

  const argumentNode = argument => {
    const argumentSteps = argument.map((step, key) => {
      const justifier = step.justifiers.length == 0 ?
        'premise' : 'from ' + step.justifiers.join(', ')
      return (
        <div key={key}>
          ({step.index}) {step.proposition} [{justifier}; {step.truth}]
          {
            step.justifiers.length == 0 ?
              <button
                className={smallButtonClassNames}
                onClick={() => handleExpandPremise(step.index)}>
                expand
              </button> :
              <button
                className={smallButtonClassNames}
                onClick={() => handleExpandInference(step.index)}>
                explicit
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
        <div className={headingClassNames}>
          Argument: 
          <button
            className={smallButtonClassNames + " font-normal"}
            onClick={() => {
              setUserMode('inputProposition')
              // disable send button
            }}>
            input
          </button>
        </div>
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

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          {!theses.thesis ? undefined : thesesDiv}
          {args.argument.length == 0 ? undefined : argumentsDiv}
          {!lastPrompt ? undefined : 
            <>
              <div className={headingClassNames}>Last:</div>
              <div>{lastPrompt}</div>
            </>
          }
        </div>
      </div>
      {loadingIndicator}
      <div ref={bottomRef} />
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
