import './App.css'
import {useImmer} from 'use-immer'
import {useState, useEffect} from 'react'

import type {ConversationType, FileType} from './types'

import Conversation from './Conversation'
import FileDropUpload from './FileDropUpload'
import { ChevronsRight } from 'lucide-react'

const initialState: ConversationType = {
  id: 1,
  name: '',
  initPrompt: undefined,
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

  const createConversation = (initPrompt?: string) => {
    setConversations(c => {c.push({
      ...initialState, 
      id: nextConvId, 
      initPrompt
    })})
    setNextConvId(i => i = i+1)
    setCurrConvIndex(conversations.length)
  }

  const createConversationFromProposition = (proposition: string) => {
    createConversation(proposition)
  }

  const selectConversation = (index: number) => {
    setCurrConvIndex(index)
  }

  const newFileUploaded = (newFile: FileType) => {
    setFiles(f => {f.push(newFile)})
  }

  const associateFileToConversation = (file_id: string) => {
    setConversations(c => {
      const conv = c[currConvIndex]
      const currentSnapshot = conv.snapshots[conv.snapshots.length - 1]
      if (currentSnapshot && !currentSnapshot.file_ids.includes(file_id)) {
        currentSnapshot.file_ids.push(file_id)
      }
      setPaneOpened(false)
    })
  }

  useEffect(() => {
    if (paneOpened) {
      setPaneOpened(false)
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
        flex flex-col items-start w-[250px] bg-slate-200 dark:bg-zinc-800
        fixed lg:relative h-full z-40 transition-all duration-300 max-lg:pt-15
        ${paneOpened ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <h1 className="text-xl font-bold text-zinc-700 dark:text-zinc-300 ml-2 mt-4 mb-2">
          Dianoia
        </h1>
        <button
          tabIndex={3}
          className='px-4 py-2 ml-2 mt-2 mb-4 text-white bg-indigo-500 border-none rounded-xl'
          onClick={() => createConversation()}>
          New
        </button>
        {conversations.map((conv, index) => (
          <button
            key={index}
            className={`
              w-[100%] text-left p-2 text-zinc-700 dark:text-zinc-300 border-none
              hover:bg-slate-300 dark:hover:bg-zinc-700
              ${
                conv.id == currConvIndex + 1 ?
                'bg-slate-300 dark:bg-zinc-700' : ''
              }
            `}
            onClick={() => selectConversation(index)}>
            {conv.name || 'New Thesis'}
          </button>
        ))}
        <FileDropUpload newFileUploaded={newFileUploaded}/>
        {files.map((file, index) => (
          <div
            key={index}
            className={`w-[100%] flex items-center justify-between 
              rounded-md p-2 text-zinc-700 dark:text-zinc-300 border-none`}
          >
            <span 
              className="flex-1 text-left overflow-hidden max-h-12" 
              style={{textOverflow: 'ellipsis'}}
              title={file.filename}
            >
              {file.filename}
            </span>
            <button
              className="ml-2 p-1 hover:bg-slate-300 dark:hover:bg-zinc-700 rounded"
              onClick={() => associateFileToConversation(file.file_id)}
            >
              <ChevronsRight size={18} />
            </button>
          </div>
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
          createConversationFromProposition={createConversationFromProposition}
          files={files}
        />
      </div>
    </div>
  )
}

export default App
