// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
import './App.css'

import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [message, setMessage] = useState('')

  useEffect(() => {
    axios.get('http://localhost:8000/api/hello')
      .then(response => {
        setMessage(response.data.message)
      })
      .catch(error => {
        console.error('Error fetching message:', error)
      })
  }, [])

  return <h1>{message}</h1>
}

export default App
