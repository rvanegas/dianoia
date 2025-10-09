import './App.css'
// import React, {createContext, useReducer, useContext} from 'react'

import type { ConversationType } from './types'

import Conversation from './Conversation'

const initialState: ConversationType = {
  index: 1,
  name: '',
  snapshots: []
}

function App() {
  const newConversation = (index: string, proposition: string) => {
    console.log(`newConversation ${index} ${proposition} ${initialState}`)
  }

  return (
    <div className="flex w-[100dvw] h-[100dvh]">
      <div className="flex flex-col items-center w-[250px] bg-slate-200 dark:bg-zinc-800 lg:block hidden">
        <button className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'>
          New Chat
        </button>
      </div>
      <div className="flex flex-1 flex-col h-[100%] w-[100%] bg-white items-center" >
        <Conversation newConversation={newConversation}/>
      </div>
    </div>
  )
}

export default App
