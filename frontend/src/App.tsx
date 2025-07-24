import './App.css'
import {useImmer} from 'use-immer'
import {useState, useEffect} from 'react'

import type {ConversationType, FileType} from './types'

import Conversation from './Conversation'
import FileDropUpload from './FileDropUpload'

const initialState: ConversationType = {
  id: 1,
  name: '',
  initPrompt: undefined,
  vector_store_id: undefined,
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

  const createConversation = ({initPrompt, vector_store_id}: {
    initPrompt?: string,
    vector_store_id?: string,
  }) => {
    setConversations(c => {c.push({
      ...initialState, 
      id: nextConvId, 
      initPrompt,
      vector_store_id
    })})
    setNextConvId(i => i = i+1)
    setCurrConvIndex(conversations.length)
  }

  const createConversationFromProposition = (proposition: string) => {
    createConversation({initPrompt: proposition})
  }

  const createConversationFromFile = (index: number) => {
    createConversation({vector_store_id: files[index].vector_store_id})
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
      onClick={(e) => {
        e.stopPropagation()
        setPaneOpened(!paneOpened)
      }}
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
        tabIndex={3}
          className='w-[90%] px-2 py-2 m-4 text-white bg-indigo-500 border-none rounded-xl'
          onClick={() => createConversation({initPrompt: ''})}>
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
            {conv.name || 'New Thesis'}
          </button>
        ))}
        <FileDropUpload newFileUploaded={newFileUploaded}/>
        {files.map((file, index) => (
          <button
            key={index}
            className="w-[100%] text-left rounded-md p-2 text-zinc-700 dark:text-zinc-300
              border-none hover:bg-slate-300 dark:hover:bg-zinc-700"
            onClick={() => createConversationFromFile(index)}>
            Create from {file.filename}
          </button>
        ))}
      </div>
      <div
        className="flex flex-1 flex-col h-[100%] w-[100%] bg-white items-center max-lg:pt-15 dark:bg-zinc-900"
        onClick={() => window.innerWidth < 1024 && setPaneOpened(false)}
      >
        {paneButton}
        <Conversation
          key={currConvIndex}
          conversation={conversations[currConvIndex]}
          setConversation={setConversation}
          createConversationFromProposition={createConversationFromProposition}/>
      </div>
    </div>
  )
}

export default App
