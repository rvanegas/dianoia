// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState('')
  const [prompt, setPrompt] = useState('')
  const [reply, setReply] = useState('')

  useEffect(() => {
    axios.get('http://localhost:8000/api/hello')
      .then(response => {
        setMessage(response.data.message)
      })
      .catch(error => {
        console.error('Error fetching message:', error)
      })
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await axios.post('http://localhost:8000/api/chat', {prompt})
      setReply(response.data.reply)
    } catch (error) {
      console.log('Error: ', error)
    }
  }

  return (
    <div>
      <h1>{message}</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="Ask the LLM"
        />
        <button type="submit">Send</button>
      </form>
      <p>Reply: {reply}</p>
    </div>
  );
}

export default App
