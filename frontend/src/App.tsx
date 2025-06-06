// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])

  const handleSend = async () => {
    if (!input.trim()) return
    const userMessage = { sender: 'user', text: input }
    setMessages(prev => [...prev, userMessage])

    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input })
    });
    const data = await response.json()
    const botMessage = { sender: 'bot', text: data.response }
    setMessages(prev => [...prev, botMessage])
    setInput('')
  };

  //   try {
  //     const response = await axios.post('http://localhost:8000/api/chat', {prompt})
  //     setReply(response.data.reply)
  //   } catch (error) {
  //     console.log('Error: ', error)
  //   }
  // }

  return (
    <div className="p-4 max-w-lg mx-auto">
      <div className="border rounded p-4 h-96 overflow-y-scroll bg-white shadow">
        {messages.map((m, i) => (
          <div key={i} className={`my-2 ${m.sender === 'user' ? 'text-right' : 'text-left'}`}>
            <span className={`inline-block px-3 py-1 rounded ${m.sender === 'user' ? 'bg-blue-100' : 'bg-gray-100'}`}>
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="flex mt-4">
        <input
          className="flex-1 border rounded p-2 mr-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={handleSend} className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">Send</button>
      </div>
    </div>
  );
}

export default App
