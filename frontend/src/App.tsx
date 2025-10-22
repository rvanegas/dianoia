import './App.css'
import {useImmer} from 'use-immer'
import {useState, useEffect} from 'react'

import type {ConversationType, FileType} from './types'

import Conversation from './Conversation'
import FileDropUpload from './FileDropUpload'

const initialState: ConversationType = {
  id: 1,
  name: '',
  initPrompt: '',
  snapshots: []
}

function App() {
  const [conversations, setConversations] = useImmer<ConversationType[]>(
    [{...initialState, id: 1}])
  const [nextConvId, setNextConvId] = useImmer<number>(2)
  const [currConvIndex, setCurrConvIndex] = useImmer<number>(0)
  const [files, setFiles] = useImmer<FileType[]>([])
  const [paneOpened, setPaneOpened] = useState<boolean>(false)

  const setConversation = (newConversation: ConversationType) => {
    setConversations(c => {c[currConvIndex] = newConversation})
  }

  const createConversation = (proposition: string) => {
    setConversations(c => {c.push({...initialState, id: nextConvId, initPrompt: proposition})})
    setNextConvId(i => i = i+1)
    setCurrConvIndex(conversations.length)
  }

  const createConversationFromFile = (index: number) => {
    console.log(index)
  }

  const selectConversation = (index: number) => {
    setCurrConvIndex(index)
  }

  const newFileUploaded = (newFile: FileType) => {
    setFiles(f => {f.push(newFile)})
  }

  useEffect(() => {
    if (paneOpened) {
      setPaneOpened(!paneOpened)
    }
  }, [currConvIndex])

  const paneButton = (
    <button
      className='lg:hidden fixed top-4 left-4 z-50 p-2 bg-indigo-600 text-white rounded-md'
      onClick={() => setPaneOpened(!paneOpened)}
    >
      {'\u2630'}
    </button>
  )

  return (
    <div className="flex w-[100dvw] h-[100dvh]">
      <div className={`
        flex flex-col items-start px-2 w-[250px] bg-slate-200 dark:bg-zinc-800
        fixed lg:relative h-full z-40 transition-all duration-300 max-lg:pt-15
        ${paneOpened ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <button
          className='w-[90%] px-2 py-2 m-4 text-white bg-indigo-500 border-none rounded-xl'
          onClick={() => createConversation('')}>
          New
        </button>
        {conversations.map((conv, index) => (
          <button
            key={index}
            className={`
              w-[100%] text-left rounded-md p-2 text-zinc-700 dark:text-zinc-300 border-none
              hover:bg-slate-300 dark:hover:bg-zinc-700
              ${
                conv.id == currConvIndex + 1 ?
                'border-indigo-500 border-solid border-2' : 'border-none'
              }
            `}
            onClick={() => selectConversation(index)}>
            Select {conv.id}
          </button>
        ))}
        {files.map((file, index) => (
          <button
            key={index}
            className="w-[100%] text-left rounded-md p-2 text-zinc-700 dark:text-zinc-300
              border-none hover:bg-slate-300 dark:hover:bg-zinc-700"
            onClick={() => createConversationFromFile(index)}>
            Create from {file.filename}
          </button>
        ))}
        <FileDropUpload newFileUploaded={newFileUploaded}/>
      </div>
      <div className="flex flex-1 flex-col h-[100%] w-[100%] bg-white items-center max-lg:pt-15 dark:bg-zinc-900">
        {paneButton}
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
