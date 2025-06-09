// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [prompt, setPrompt] = useState('')
  const [messages, setMessages] = useState([])

  const handleSend = async () => {
    if (!prompt.trim()) return
    const userMessage = { role: 'user', content: prompt }
    const newMessages = [...messages, userMessage]
    setMessages(prev => newMessages)
    try {
      const response = await axios.post('http://localhost:8000/api/chat', {prompt, history: newMessages})
      const botMessage = { role: 'assistant', content: response.data.reply }
      setMessages(prev => [...newMessages, botMessage])
      setPrompt('')
    } catch (error) {
      console.log('Error: ', error)
    }
  }

  return (
    <div className="p-4 max-w-lg mx-auto">
      <div className="border border-zinc-600 rounded p-4 h-96 overflow-y-scroll bg-white dark:bg-zinc-800 shadow">
        {messages.map((m, i) => (
          <div key={i} className={`my-2 ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <p className={`${m.role == 'user' ? 'text-indigo-400' : 'text-slate-500 dark:text-gray-400'}`}>
              {m.role === 'user'? 'You' : 'Dianioia'}
            </p>
            <p className={`inline-block px-3 py-1 rounded-md ${m.role === 'user' ? 'bg-indigo-400' : 'bg-slate-200 text-slate-700 dark:bg-gray-600 dark:text-slate-100'}`}>
              {m.content}
            </p>
          </div>
        ))}
      </div>
      <div className="flex mt-4">
        <input
          className="flex-1 border border-zinc-600 rounded-md p-2 mr-2 text-gray-700 dark:text-gray-200"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={handleSend} className="bg-indigo-600 text-white font-bold px-4 py-2 rounded-md hover:bg-indigo-500">Send</button>
      </div>
    </div>
  )
}

export default App
