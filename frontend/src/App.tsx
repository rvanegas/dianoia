import './App.css'
import {useImmer} from 'use-immer'

import type {ConversationType} from './types'

import Conversation from './Conversation'

const initialState: ConversationType = {
  id: 1,
  name: '',
  initPrompt: '',
  snapshots: []
}

function App() {
  const [conversations, setConversations] = useImmer<ConversationType[]>(
    [{...initialState, id: 1}, {...initialState, id: 2}])
  const [nextConvId, setNextConvId] = useImmer<number>(3)
  const [currConvIndex, setCurrConvIndex] = useImmer<number>(0)

  const setConversation = (newConversation: ConversationType) => {
    setConversations(c => {c[currConvIndex] = newConversation})
  }

  const createConversation = (proposition: string) => {
    setConversations(c => {c.push({...initialState, id: nextConvId, initPrompt: proposition})})
    setNextConvId(i => i = i+1)
    setCurrConvIndex(conversations.length)
  }

  const selectConversation = (index: number) => {
    setCurrConvIndex(index)
  }

  // console.log('x', conversations, nextConvId, currConvIndex)

  return (
    <div className="flex w-[100dvw] h-[100dvh]">
      <div className="flex flex-col items-center w-[250px] bg-slate-200 dark:bg-zinc-800 lg:block hidden">
        <button
          className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'
          onClick={() => createConversation('')}>
          New
        </button>
        {conversations.map((conv, index) => (
          <button
            key={conv.id}
            className='w-[80%] px-2 py-4 m-4 text-white bg-indigo-500 border-none rounded-2xl'
            onClick={() => selectConversation(index)}>
            Select {conv.id}
          </button>
        ))}
      </div>
      <div className="flex flex-1 flex-col h-[100%] w-[100%] bg-white items-center">
        <Conversation
          key={currConvIndex}
          conversation={conversations[currConvIndex]}
          setConversation={setConversation}
          createConversation={createConversation}/>
      </div>
    </div>
  )
}

export default App
