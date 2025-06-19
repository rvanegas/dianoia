import './App.css'

import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'

import { exportMarkdown } from './markdown.tsx'

type Message = {
  role: 'user' | 'assistant';
  content: string;
}

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

function ExpandPremiseButton({handleExpandPremise}) {
  return (
    <button
      onClick={handleExpandPremise}
      className="inline text-xs px-1 py-0.5 text-transparent
        hover:text-black focus:outline-none">
      Expand
    </button>
  )
}

function Theses({content}) {
  const theses = JSON.parse(content)
  return (
    <div>
      <div className="text-lg font-bold">Thesis:</div>
      <div>{theses.thesis}</div>
      <div className="text-lg font-bold">Counter-Thesis:</div>
      <div>{theses.counter_thesis}</div>
      <div className="text-lg font-bold">Explanation:</div>
      <div>{theses.explanation}</div>
    </div>
  )
}

function Arguments({content, handleExpandPremise}) {
  const arguments_ = JSON.parse(content)

  const argumentNode = argument => {
    const argumentSteps = argument.map((step, key) => {
      const justifier = step.justifiers.length == 0 ?
        'premise' : 'from ' + step.justifiers.join(', ')
      return (
        <div key={key}>
          ({step.index}) {step.proposition} [{justifier}]
          {
            step.justifiers.length != 0 ? undefined :
              <ExpandPremiseButton
                handleExpandPremise={() => handleExpandPremise(step.index)}>
              </ExpandPremiseButton>
          }
        </div>
      )
    })
    return <div>{argumentSteps}</div>
  }

  return (
    <div>
      <div>
        <div className="text-lg font-bold">Argument:</div>
        <div>{argumentNode(arguments_.argument)}</div>
      </div>
      {
        arguments_.counter_argument.length == 0 ? undefined :
        <div>
          <div className="text-lg font-bold">Counter-Argument:</div>
          <div>{argumentNode(arguments_.counter_argument)}</div>
        </div>
      }
      <div className="text-lg font-bold">Explanation:</div>
      <div>{arguments_.explanation}</div>
    </div>
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
      className="bg-indigo-600 text-white font-bold
        px-4 py-2 rounded-md hover:bg-indigo-500">
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function App() {
  const [prompt, setPrompt] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const handleSend = async ({internalPrompt}) => {
    const content = internalPrompt ? internalPrompt : prompt
    if (!content.trim()) return
    const userMessage: Message = {role: 'user', content}
    const newMessages = [...messages, userMessage]
    setPrompt('')
    setMessages(prev => newMessages)
    setLoading(true)
    try {
      const url = `${VITE_API_BASE_URL}/api/v1/chat`
      const response = await axios.post(url, {history: newMessages})
      const botMessage: Message = {
        role: 'assistant',
        content: response.data.reply,
      }
      setMessages(prev => [...newMessages, botMessage])
      setPrompt('')
    } catch (error) {
      console.log('Error: ', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExpandPremise = async (index) => {
    handleSend({
      internalPrompt: `Introduce one or more premises from ` +
        `which proposition (${index}) is inferred.`
    })
  }

  const handleBack = () => {
    const lastUserMessageIndex = messages.findLastIndex(m => m.role == 'user')
    setMessages(messages.slice(0, lastUserMessageIndex))
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({behavior: 'smooth'})
  }, [messages, loading])

  // window.xmessages = messages

  return (
    <div className="px-4  pt-4 max-w-[720px] size-full max-h-[90vh] flex flex-col">
      <div className="rounded px-4 h-screen overflow-y-scroll bg-white dark:bg-zinc-800">
        {messages.map((m, i) => (
          <div
            key={i}
            className={m.role === 'user' ? 'my-2 text-right' : 'my-2 text-left'}>
            <p
              className={`${
                m.role == "user"
                  ? "text-indigo-600"
                  : "text-slate-500 dark:text-gray-400"
              }`}>
              {m.role === "user" ? "You" : "Dianoia"}
            </p>
            {m.role == 'assistant' ? (
              <div className="bg-slate-100 dark:bg-zinc-700 rounded-md text-zinc-700 p-3">
                <div className="prose dark:prose-invert max-w-none">
                  {
                    i == 1
                      ? <Theses content={m.content}></Theses>
                      : <Arguments
                          content={m.content}
                          handleExpandPremise={handleExpandPremise}>
                        </Arguments>
                  }
                </div>
              </div>
            ) : (
              <p className="inline-block px-3 py-1 rounded-md bg-indigo-400 text-indigo-50">
                {m.content}
              </p>
            )}
          </div>
        ))}
        {loading && (
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
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex mt-4">
        <input
          className="flex-1 border border-zinc-600 rounded-md p-2 mr-2 text-gray-700 dark:text-gray-200"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
            if (e.key == "Enter") {
              handleSend()
              e.preventDefault()
            }
          }}
          placeholder="Type your message..."
        />
        <button
          onClick={handleSend}
          className="bg-indigo-600 text-white font-bold
            px-4 py-2 rounded-md hover:bg-indigo-500">
          Send
        </button>
        <button
          onClick={handleBack}
          className="bg-indigo-600 text-white font-bold
            px-4 py-2 rounded-md hover:bg-indigo-500">
          Back
        </button>
        <ExportButton textCallback={() => exportMarkdown(messages)}/>
      </div>
    </div>
  )
}

export default App
