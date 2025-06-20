import "./App.css";

import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import MessageBubble from "./components/MessageBubble.tsx";
import { FiSend, FiDelete, FiClipboard, FiCheck } from 'react-icons/fi';

import { exportMarkdown } from './markdown.tsx'

type Message = {
  role: "user" | "assistant"
  content: string
};

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

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

function ExpandInferenceButton({handleExpandInference}) {
  return (
    <button
      onClick={handleExpandInference}
      className="inline text-xs px-1 py-0.5 text-transparent
        hover:text-black focus:outline-none">
      Explicit
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

function Arguments({content, handleExpandPremise, handleExpandInference}) {
  const arguments_ = JSON.parse(content)

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
      className="flex flex-col items-center justify-center bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors w-[45px]">
      {copied ? <FiCheck className="h-5 w-5" /> : <FiClipboard className="h-5 w-5" />}
    </button>
  )
}

function App() {
  const [prompt, setPrompt] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const handleSend = async ({ internalPrompt }) => {
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
        role: "assistant",
        content: response.data.reply,
      };
      setMessages([...newMessages, botMessage])
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleExpandPremise = async (index) => {
    handleSend({
      internalPrompt: `Introduce one or two premises from ` +
        `which proposition (${index}) is inferred.`
    })
  }

  const handleExpandInference = async (index) => {
    handleSend({
      internalPrompt: `If the inference from which proposition ` +
        `(${index}) is inferred is not strictly deductive, introduce ` +
        `one or two premises to make the inference more explicit.`
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
    <div className="flex w-[100dvw] h-[100dvh]">
      {/* Left Sidebar - empty div as requested */}
      <div className="flex flex-col items-center w-[250px] bg-slate-100 dark:bg-zinc-800" id='sidebar'>
        {/* Sidebar content would go here */}
        <button className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'>
          New Chat
        </button>
      </div>

      {/* Main Chat Area */}
      <div className=" flex flex-1 flex-col h-[100%] w-[100%] items-center" >
        {/* Message bubbles area */}
        <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide">
          {/* Example message bubbles - you would map through actual messages here */}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[85%] ${m.role == 'user' ? 'self-end' : 'self-start'}`}>
              <p
                className={`${
                  m.role == "user"
                    ? "text-indigo-600 text-right"
                    : "text-slate-500 dark:text-gray-400"
                }`}>
                {m.role === "user" ? "You" : "Dianoia"}
              </p>
              {m.role == 'assistant' ? (
                <div className="bg-slate-100 dark:bg-zinc-700 rounded-3xl rounded-tl-none text-zinc-700 p-2 py-4">
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
                <p className="inline-block px-3 py-1 rounded-3xl rounded-tr-none bg-indigo-400 text-indigo-50">
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

        {/* Input area fixed at the bottom */}
        <div className="p-4 flex gap-2 h-[10%] w-[100%]">
          <input 
            type="text" 
            placeholder="Type your message here..." 
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key == "Enter") {
                handleSend({internalPrompt: ''});
                e.preventDefault();
              }
            }}
            className="flex-1 px-4 bg-slate-100 rounded-full focus:outline-none"
          />
          <button className="flex flex-col items-center justify-center bg-indigo-500 text-white rounded-full hover:bg-indigo-600 transition-colors w-[45px]">
            <FiSend className="h-5 w-5" />
          </button>
          <button
            onClick={handleBack}
            className="flex flex-col items-center justify-center bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors w-[45px]">
            <FiDelete className="h-5 w-5 " />
          </button>
          <ExportButton textCallback={() => exportMarkdown(messages)}/>
        </div>
      </div>
    </div>
  );
}

export default App;
