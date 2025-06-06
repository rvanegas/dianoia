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
      <div className="border rounded p-4 h-96 overflow-y-scroll bg-white shadow">
        {messages.map((m, i) => (
          <div key={i} className={`my-2 ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <span className={`inline-block px-3 py-1 rounded ${m.role === 'user' ? 'bg-blue-100' : 'bg-gray-100'}`}>
              {m.content}
            </span>
          </div>
        ))}
      </div>
      <div className="flex mt-4">
        <input
          className="flex-1 border rounded p-2 mr-2"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={handleSend} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">Send</button>
      </div>
    </div>
  )
}

export default App
