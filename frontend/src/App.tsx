import "./App.css";

import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import MessageBubble from "./components/MessageBubble.tsx";
import { FiSend, FiDelete, FiClipboard, FiCheck } from 'react-icons/fi';

import { thesisMarkdown, developmentMarkdown, exportMarkdown } from './markdown.tsx'

type Message = {
  role: "user" | "assistant"
  content: string
};

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

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

  const handleSend = async () => {
    if (!prompt.trim()) return
    setPrompt('')
    const userMessage: Message = { role: "user", content: prompt }
    const newMessages = [...messages, userMessage]
    setMessages(prev => newMessages)
    setLoading(true)

    try {
      const response = await axios.post(`${VITE_API_BASE_URL}/api/v1/chat`, {
        history: newMessages,
      });

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

  const handleBack = () => {
    const lastUserMessageIndex = messages.findLastIndex(m => m.role == 'user')
    setMessages(messages.slice(0, lastUserMessageIndex))
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // window.xmessages = messages

  return (
    <div className="flex w-[100vw] h-[100vh]">
      {/* Left Sidebar - empty div as requested */}
      <div className="flex flex-col items-center w-[250px] bg-slate-100 dark:bg-zinc-800">
        {/* Sidebar content would go here */}
        <button className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'>
          New Chat
        </button>
      </div>

      {/* Main Chat Area */}
      <div className=" flex flex-1 flex-col h-[100%] w-[100%]" >
        {/* Message bubbles area */}
        <div className="flex flex-1 overflow-y-auto p-20 flex-col gap-10 w-[100%]">
          {/* Example message bubbles - you would map through actual messages here */}
          {messages.map((msg, i) => (
            msg.role == 'user' ? 
              <MessageBubble role={msg.role} content={msg.content} key={i} />
              :
              <MessageBubble role={msg.role} content={i == 1 ? thesisMarkdown(msg.content) : developmentMarkdown(msg.content)} key={i} />
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
        <div className="p-4 flex gap-2 h-[10%]">
          <input 
            type="text" 
            placeholder="Type your message here..." 
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key == "Enter") {
                handleSend();
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
