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

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500`
const headingClassNames = `text-lg font-bold`

function ExpandPremiseButton({handleExpandPremise}) {
  return (
    <button
      onClick={handleExpandPremise}
      className={smallButtonClassNames}>
      Expand
    </button>
  )
}

function ExpandInferenceButton({handleExpandInference}) {
  return (
    <button
      onClick={handleExpandInference}
      className={smallButtonClassNames}>
      Explicit
    </button>
  )
}

function Theses({content}) {
  return (
    <>
      <div className={headingClassNames}>Thesis:</div>
      <div>{content.thesis}</div>
      <div className={headingClassNames}>Counter-Thesis:</div>
      <div>{content.counter_thesis}</div>
      <div className={headingClassNames}>Presupposition:</div>
      <div>{content.presupposition}</div>
    </>
  )
}

function Arguments({content, handleExpandPremise, handleExpandInference}) {
  const argumentNode = argument => {
    const argumentSteps = argument.map((step, key) => {
      const justifier = step.justifiers.length == 0 ?
        'premise' : 'from ' + step.justifiers.join(', ')
      return (
        <div key={key}>
          ({step.index}) {step.proposition} [{justifier}; {step.truth}]
          {
            step.justifiers.length == 0 ?
              <ExpandPremiseButton
                handleExpandPremise={() => handleExpandPremise(step.index)}>
              </ExpandPremiseButton> :
              <ExpandInferenceButton
                handleExpandInference={() => handleExpandInference(step.index)}>
              </ExpandInferenceButton>
          }
        </div>
      )
    })
    return <div>{argumentSteps}</div>
  }

  return (
    <>
      <div>
        <div className={headingClassNames}>Argument:</div>
        <div>{argumentNode(content.argument)}</div>
      </div>
      {
        content.counter_argument.length == 0 ? undefined :
        <div>
          <div className={headingClassNames}>Counter-Argument:</div>
          <div>{argumentNode(content.counter_argument)}</div>
        </div>
      }
    </>
  )
}

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
    const argumentPrompt = {prompt: content, ...args, ...theses}
    try {
      const url = `${VITE_API_BASE_URL}/api/v1/argument`
      const response = await axios.post(url, argumentPrompt)
      setArgs(JSON.parse(response.data.reply))
    } catch (error) {
      console.error('Error: ', error)
    } finally {
      setLoading(false)
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

  const handleBack = () => {
    const lastUserMessageIndex = messages.findLastIndex(m => m.role == 'user')
    setMessages(messages.slice(0, lastUserMessageIndex))
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

  const chatDiv = (
    <div className="flex w-[100dvw] h-[100dvh]">
      <div className="flex flex-col items-center w-[250px] bg-slate-200 dark:bg-zinc-800 lg:block hidden">
        <button className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'>
          New Chat
        </button>
      </div>
      <div className="flex flex-1 flex-col h-[100%] w-[100%] bg-white items-center" >
        <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5 md:px-20">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[75%] text-left ${m.role === 'user' ? 'my-2 self-end' : 'my-2 self-start'}`}>
              <p
                className={`${
                  m.role == "user"
                    ? "text-indigo-600 text-right"
                    : "text-slate-500 dark:text-gray-400 text-left"
                }`}>
                {m.role === "user" ? "You" : "Dianoia"}
              </p>
              {m.role == 'assistant' ? (
                <div className="bg-slate-100 dark:bg-zinc-700 rounded-2xl rounded-tl-none text-zinc-700 p-3">
                  <div className="prose dark:prose-invert max-w-none">
                    {
                      i == 1
                        ? <Theses content={m.content}></Theses>
                        : <Arguments
                            content={m.content}
                            handleExpandPremise={handleExpandPremise}
                            handleExpandInference={handleExpandInference}
                          >
                          </Arguments>
                    }
                  </div>
                </div>
              ) : (
                <p className="inline-block px-3 py-1 rounded-2xl rounded-tr-none bg-indigo-400 text-indigo-50">
                  {m.content}
                </p>
              )}
            </div>
          ))}
          {loadingIndicator}
          <div ref={bottomRef} />
        </div>
        <div className="p-4 flex gap-2 w-[100%] flex-wrap">
          <input
            className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-none dark:bg-zinc-800"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key == "Enter") {
                handleSend(prompt)
                e.preventDefault()
              }
            }}
            placeholder="Type your message..."
          />
          <button
            onClick={() => handleSend(prompt)}
            className={bigButtonClassNames}>
            Send
          </button>
          <button
            onClick={handleBack}
            className={bigButtonClassNames}>
            Back
          </button>
          <ExportButton textCallback={() => exportMarkdown(theses, args)}/>
        </div>
      </div>
    </div>
  )

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5 md:px-20">
      {messages.map((m, i) => (
        <div
          key={i}
          className={`max-w-[75%] text-left ${m.role === 'user' ? 'my-2 self-end' : 'my-2 self-start'}`}>
          <p
            className={`${
              m.role == "user"
                ? "text-indigo-600 text-right"
                : "text-slate-500 dark:text-gray-400 text-left"
            }`}>
            {m.role === "user" ? "You" : "Dianoia"}
          </p>
          {m.role == 'assistant' ? (
            <div className="bg-slate-100 dark:bg-zinc-700 rounded-2xl rounded-tl-none text-zinc-700 p-3">
              <div className="prose dark:prose-invert max-w-none">
                {
                  i == 1
                    ? <Theses content={m.content}></Theses>
                    : <Arguments
                        content={m.content}
                        handleExpandPremise={handleExpandPremise}
                        handleExpandInference={handleExpandInference}
                      >
                      </Arguments>
                }
              </div>
            </div>
          ) : (
            <p className="inline-block px-3 py-1 rounded-2xl rounded-tr-none bg-indigo-400 text-indigo-50">
              {m.content}
            </p>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )

  const userDiv = (
    <div className="p-4 flex gap-2 w-[100%] flex-wrap">
      <input
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-none dark:bg-zinc-800"
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key == "Enter") {
            handleSend(prompt)
            e.preventDefault()
          }
        }}
        placeholder="Type your message..."
      />
      <button
        onClick={() => handleSend(prompt)}
        className={bigButtonClassNames}>
        Send
      </button>
      <button
        onClick={handleBack}
        className={bigButtonClassNames}>
        Back
      </button>
      <ExportButton textCallback={() => exportMarkdown(theses, args)}/>
    </div>
  )

  const newMessagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          {!theses.thesis ? undefined : <Theses content={theses}/>}
          {args.argument.length == 0 ? undefined :
            <Arguments
              content={args}
              handleExpandPremise={handleExpandPremise}
              handleExpandInference={handleExpandInference}
            >
            </Arguments>
          }
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
        {newMessagesDiv}
        {userDiv}
      </div>
    </div>
  )

  return frameDiv
}

export default App
