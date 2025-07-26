import './App.css'

import {useEffect, useRef, useState} from 'react'
import {Menu} from '@headlessui/react';
import {ChevronDown } from 'lucide-react';
import axios from 'axios'

import type {StepType, ArgMode, ConversationSnapshot,
  ConversationType, FileType} from './types'
import {exportMarkdown} from './markdown'

type UserMode = 'waiting' | 'ready' | 'input'
type ActionType = 'remove' | 'assume' | 'explain'

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500 disabled:opacity-[25%]`
const headingClassNames = `text-lg font-bold`

function initialSnapshot() : ConversationSnapshot {
  return {
    thesis: '',
    counter_thesis: '',
    presupposition: '',
    assumptions: [],
    argument: [],
    counter_argument: [],
    lastPrompt: '',
    evaluationsPending: false,
    explanation: '',
    formalization: [],
    argMode: 'thesis',
    file_ids: [],
  }
}

const actionOptions = [
  {
    label: 'Move to Assumptions',
    value: 'assume',
  },
  {
    label: 'Remove from Argument',
    value: 'remove',
  },
  {
    label: 'Request Justifying Propositions from LLM',
    value: 'ai-justify',
  },
  {
    label: 'Introduce Justifying Proposition',
    value: 'user-justify',
  },
  {
    label: 'Create New Conversation with this Proposition',
    value: 'dispute',
  },
]

function Conversation({
  conversation,
  setConversation,
  createConversationFromProposition,
  files
}: {
  conversation: ConversationType,
  setConversation: (newConversation: ConversationType) => void,
  createConversationFromProposition: (proposition: string) => void,
  files: FileType[]
}) {
  const snapshotRenderCount = useRef(0)
  const [snapshotIndex, setSnapshotIndex] = useState<number>(conversation.snapshots.length - 1)
  const lastSnapshot = conversation.snapshots[snapshotIndex]
  const currentSnapshot: ConversationSnapshot = lastSnapshot ?
    lastSnapshot : initialSnapshot()

  // ready/waiting/input
  const [userMode, setUserMode] = useState<UserMode>('ready')

  // used by input to save which user-justify action was selected
  const [targetLoc, setTargetLoc] = useState<string>('')
  const [targetIndex, setTargetIndex] = useState<number>(0)

  // contents of input element
  const [inputText, setInputText] = useState<string>('')

  // should rename to currentPrompt. this is prompt backend is currently working on.
  const [prompt, setPrompt] = useState<string>('')

  // export button
  const [copied, setCopied] = useState<boolean>(false)

  // input reference 
  const inputRef = useRef<HTMLInputElement>(null)

  // this saves new versions of argument. if inplace is true, then only annotations
  // should change
  const saveSnapshot = (newSnap: ConversationSnapshot, inPlace: boolean = false, convName: string = '') => {
    const oldSnaps = conversation.snapshots
    let newSnaps
    if (inPlace) {
      newSnaps = [...oldSnaps.slice(0, snapshotIndex), newSnap,
        ...oldSnaps.slice(snapshotIndex + 1)]
    }
    else {
      newSnaps = [...oldSnaps.slice(0, snapshotIndex + 1), newSnap]
      snapshotRenderCount.current += 1
      setSnapshotIndex(prev => prev + 1)
    }
    const newConversation = {...conversation, snapshots: newSnaps}
    if (convName) newConversation.name = convName
    setConversation(newConversation)
  }

  // this is just an abbreviation to keep typescript happy
  const argLoc = (loc: string) => {
    return currentSnapshot[loc as keyof typeof currentSnapshot] as any[]
  }

  const handleThesis = async (content?: string) => {
    if (userMode == 'waiting') return
    if (!(content && content.trim())) return
    setPrompt(content)
    setUserMode('waiting')
    setInputText('')
    const apiPrompt = {
      ...currentSnapshot,
      proposition: content,
    }
    const path = '/api/v1/theses'
    const url = VITE_API_BASE_URL + path
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const argMode : ArgMode = 'thesis'
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        lastPrompt: content,
        argMode,
      }
      saveSnapshot(newSnapshot, false, responseObject.name)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleAIJustify = async (loc: string, index: number) =>
  {
    const lastPrompt = `AI Justify proposition ${argLoc(loc)[index].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/ai-justify'
    const apiPrompt = {
      ...currentSnapshot,
      loc, index
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        evaluationsPending: true,
        lastPrompt,
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleArgue = async (thesisAttr: string) => {
    if (!['thesis', 'counter_thesis'].includes(thesisAttr)) {
      throw new Error('bad params')
    }
    const argumentAttr = thesisAttr == 'thesis' ? 'argument' : 'counter_argument'
    const thesisLabel = thesisAttr == 'thesis' ? 'Thesis' : 'Counter-Thesis'
    const lastPrompt = `Argue for ${thesisLabel}`
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/argue'
    const argMode: ArgMode = 'development'
    let apiPrompt = {
      ...currentSnapshot, 
      loc: argumentAttr, index: 0,
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        argMode,
        lastPrompt
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleUserJustify = async (proposition: string) => {
    const lastPrompt = `User Justify proposition ${argLoc(targetLoc)[targetIndex].symbol}`
    setPrompt(lastPrompt)
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/user-justify'
    let apiPrompt = {
      ...currentSnapshot, 
      loc: targetLoc, index: targetIndex,
      proposition
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)

      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        evaluationsPending: true,
        lastPrompt
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  // verify that user hasn't moved away and potentially replaced 
  // contents of this snapshot. saveSnapshot() is then called 
  // with inPlace = true
  const evaluateSteps = async () => {
    const url = VITE_API_BASE_URL + '/api/v1/evaluate'
    try {
      const currentSnapshotRenderCount = snapshotRenderCount.current
      const response = await axios.post(url, currentSnapshot)
      if (currentSnapshotRenderCount != snapshotRenderCount.current) return
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        evaluationsPending: false,
      }
      saveSnapshot(newSnapshot, true)
    }
    catch (error) {
      console.error('Error: ', error)
    }
  }

  const handleAction = async (
    action: ActionType, lastPrompt: string, loc: string, index: number
  ) => {
    setUserMode('waiting')
    const url = VITE_API_BASE_URL + '/api/v1/' + action
    let apiPrompt = {
      ...currentSnapshot,
      loc, index
    }
    try {
      const response = await axios.post(url, apiPrompt)
      const responseObject = JSON.parse(response.data.reply)
      if (!responseObject) {
        throw new Error('empty responseObject')
      }
      const newSnapshot = {
        ...currentSnapshot,
        ...responseObject,
        lastPrompt
      }
      if (action == 'remove' || action == 'assume') {
        newSnapshot.evaluationsPending = true
      }
      else {
        setPrompt(lastPrompt)
      }
      saveSnapshot(newSnapshot)
      setPrompt('')
    }
    catch (error) {
      console.error('Error: ', error)
    }
    finally {
      setUserMode('ready')
    }
  }

  const handleDispute = async (step: StepType) => {
    createConversationFromProposition(step.proposition)
  }

  const handleUndo = () => {
    if (snapshotIndex <= 0) return
    const newIndex = snapshotIndex - 1
    snapshotRenderCount.current += 1
    setSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  const handleRedo = () => {
    if (snapshotIndex >= conversation.snapshots.length - 1) return
    const newIndex = snapshotIndex + 1
    snapshotRenderCount.current += 1
    setSnapshotIndex(newIndex)
    setUserMode('ready')
  }

  const handleCopy = async () => {
    const text = exportMarkdown(currentSnapshot)
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 3000)
  }

  const bottomRef = useRef<HTMLDivElement | null>(null)
  useEffect(() => {
    if (userMode == 'waiting') {
      bottomRef.current?.scrollIntoView({behavior: 'smooth'})
    }
    
    if (inputRef.current && (userMode == 'ready' || userMode == 'input')) {
      inputRef.current.focus()
    }
  }, [userMode])

  const hasFirstSnapshot = useRef(false)
  const hasCalledTheses = useRef(false)
  useEffect(() => {
    if (snapshotIndex == -1 && !hasFirstSnapshot.current) {
      hasFirstSnapshot.current = true
      saveSnapshot(currentSnapshot)
    }
    if (snapshotIndex == 0 && !hasCalledTheses.current) {
      hasCalledTheses.current = true
      if (conversation.initPrompt) {
        handleThesis(conversation.initPrompt)
      }
    }
  }, [snapshotIndex])

  useEffect(() => {
    if (currentSnapshot.evaluationsPending) {
      evaluateSteps()
    }
  }, [currentSnapshot.evaluationsPending])

  const loadingIndicator = userMode != 'waiting' ? undefined : (
    <div className="mt-2 flex items-center space-x-4">
      <span className="text-sm text-zinc-400 italic">
        Dianoia is thinking
      </span>
      <span className="typing-indicator">
        <span className="typing-dot"></span>
        <span className="typing-dot"></span>
        <span className="typing-dot"></span>
      </span>
    </div>
  )

  // ActionsMenu component with proper hooks
  const ActionsMenu = () => {
    const [showAbove, setShowAbove] = useState(false);
    const buttonRef = useRef<HTMLButtonElement>(null);

    const updatePosition = () => {
      if (buttonRef.current) {
        const rect = buttonRef.current.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const threshold = viewportHeight * 0.5; // Show above if button is within 300px of bottom
        
        setShowAbove(rect.top > threshold);
      }
    };

    useEffect(() => {
      updatePosition();
      window.addEventListener('resize', updatePosition);
      window.addEventListener('scroll', updatePosition);
      return () => {
        window.removeEventListener('resize', updatePosition);
        window.removeEventListener('scroll', updatePosition);
      };
    }, []);

    return (
      <Menu as="div" className="relative inline-block text-left">
        <Menu.Button 
          ref={buttonRef}
          className="flex items-center py-1 px-2 bg-white border rounded shadow-sm hover:bg-gray-50 hover:dark:bg-zinc-800 dark:bg-zinc-900 dark:border-zinc-800"
        >
          <ChevronDown className=" w-4 h-4" />
        </Menu.Button>

        <Menu.Items
          className={`
            absolute left-0 w-72 origin-top-right bg-white border border-gray-200
            divide-y divide-gray-100 rounded-md shadow-lg focus:outline-indigo-500 z-50
            focus:outline-2 dark:bg-zinc-900 dark:divide-zinc-800 dark:border-zinc-700
            ${showAbove 
              ? 'bottom-full mb-2' 
              : 'top-full mt-2'
            }
          `}
          style={{
            maxHeight: 'calc(100vh - 2rem)',
            overflowY: 'auto'
          }}
        >
          {actionOptions.map((option) => (
            <Menu.Item key={option.value}>
              {({ active }) => (
                <button
                  className={`
                    flex items-start w-full px-4 py-3 text-left
                    ${active ? 'bg-gray-100 dark:bg-zinc-800 text-indigo-400'
                      : 'text-gray-900 dark:text-slate-300'}
                  `}
                  onClick={() => console.log(option.value)}
                >
                  <div className="ml-3">
                    {active}
                    <div className="text-sm font-medium">{option.label}</div>
                  </div>
                </button>
              )}
            </Menu.Item>
          ))}
        </Menu.Items>
      </Menu>
    );
  };

  const actionsMenu = () => <ActionsMenu />

  const argumentNode = (loc: string, argument: StepType[]) => {
    const argumentSteps = argument.map((step, step_index) => {

      const scoreSpan = () => {
        let justifier = ''
        let value = `${step.truth}`
        if (step.justifiers.length == 0) {
          justifier = 'premise'
        }
        else {
          justifier = 'from ' + step.justifiers.join(', ')
          value += `, ${step.valid}`
        }
        const valueSpan =
          <span className={currentSnapshot.evaluationsPending ? 'line-through' : ''}>
              {value}
          </span>
        return <span>[{justifier}; {valueSpan}]</span>
      }

      return (
        <div key={step_index}>
          {actionsMenu()} ({step.symbol}) {step.proposition} {scoreSpan()}
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleAIJustify(loc, step_index)}>
            ai-justify
          </button>
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => {
              setUserMode('input')
              setTargetLoc(loc)
              setTargetIndex(step_index)
            }}>
            user-justify
          </button>
          {step_index == argument.length - 1 || step.justifiers.length != 0 ? undefined :
            <>
              <button
                key="0"
                disabled={userMode == 'waiting'}
                className={smallButtonClassNames}
                onClick={() => {
                  const prompt = `Assume proposition (${step.symbol})`
                  handleAction('assume', prompt, loc, step_index)
                }}>
                assume
              </button>
            </>
          }
          {step_index == argument.length - 1 ? undefined :
            <>
              <button
                key="1"
                disabled={userMode == 'waiting'}
                className={smallButtonClassNames}
                onClick={() => {
                  const prompt = `Remove proposition (${step.symbol})`
                  handleAction('remove', prompt, loc, step_index)
                }}>
                remove
              </button>
              <button
                key="2"
                disabled={userMode == 'waiting'}
                className={smallButtonClassNames}
                onClick={() => handleDispute(step)}>
                dispute
              </button>
            </>
          }
          {step.justifiers.length == 0 ? undefined :
            <button
              key="3"
              disabled={userMode == 'waiting'}
              className={smallButtonClassNames}
              onClick={() => {
                const prompt = `Explain inference to propositon (${step.symbol})`
                handleAction('explain', prompt, loc, step_index)
              }}>
              explain
            </button>
          }
        </div>
      )
    })
    return <div>{argumentSteps}</div>
  }

  const argumentDiv = () => (
    <div>
      <div className={headingClassNames}>Argument:</div>
      <div>{argumentNode('argument', currentSnapshot.argument)}</div>
    </div>
  )

  const counterArgumentDiv = () => (
    <div>
      <div className={headingClassNames}>Counter-Argument:</div>
      <div>{argumentNode('counter_argument', currentSnapshot.counter_argument)}</div>
    </div>
  )

  const assumptionsDiv = (
    <>
      <div className={headingClassNames}>Assumptions:</div>
      {currentSnapshot.assumptions.map((step, step_index) => (
        <div key={step_index}>
          ({step.symbol}) {step.proposition}
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => {
              const prompt = `Remove proposition (${step.symbol})`
              handleAction('remove', prompt, 'assumptions', step_index)
            }}>
            remove
          </button>
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleDispute(step)}>
            dispute
          </button>
        </div>
      ))}
    </>
  )

  const thesesDiv = (
    <>
      <div className={headingClassNames}>Thesis:</div>
      <div>
        {currentSnapshot.thesis}
        {currentSnapshot.argument.length != 0 ? undefined :
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleArgue('thesis')}>
            argue
          </button>
        }
        </div>
      <div className={headingClassNames}>Counter-Thesis:</div>
      <div>
        {currentSnapshot.counter_thesis}
        {currentSnapshot.counter_argument.length != 0 ? undefined :
          <button
            disabled={userMode == 'waiting'}
            className={smallButtonClassNames}
            onClick={() => handleArgue('counter_thesis')}>
            argue
          </button>
        }
      </div>
      <div className={headingClassNames}>Presupposition:</div>
      <div>{currentSnapshot.presupposition}</div>
    </>
  )

  const lastPromptDiv = (
    <>
      <div className={headingClassNames}>LastPrompt:</div>
      <div>{currentSnapshot.lastPrompt}</div>
    </>
  )

  const promptDiv = (
    <>
      <div className={headingClassNames}>Prompt:</div>
      <div>{prompt}</div>
    </>
  )

  const explanationDiv = () => {
    if (!currentSnapshot.formalization || currentSnapshot.formalization.length == 0) return
    return (
      <>
        <div className={headingClassNames}>Formalization:</div>
        <div>{currentSnapshot.formalization.map((prop, key) => (<div key={key}>{prop}</div>))}</div>
        <div className={headingClassNames}>Explanation:</div>
        <div>{currentSnapshot.explanation}</div>
      </>
    )
  }

  const snapshotId = snapshotIndex < 1 ? '' : `.${snapshotIndex}`

  const renderAssociatedFileNames = () => (
    <>
      <div className={headingClassNames}>Files:</div>
      <div>
        {currentSnapshot.file_ids.map(file_id => {
          const file = files.find(f => f.file_id === file_id)
          return (
            <span 
              key={file_id} 
              className="inline-block bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded mr-2 mb-1 text-sm"
            >
              {file ? file.filename : file_id}
            </span>
          )
        })}
      </div>
    </>
  );

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide px-5">
      <div className="p-3 prose dark:prose-invert max-w-none">
        <div className="max-w text-left my-2 self-start">
          <div className={headingClassNames}>Id:</div>
          <div>{conversation.id}{snapshotId}</div>
          {currentSnapshot.file_ids && currentSnapshot.file_ids.length > 0 && renderAssociatedFileNames()}
          {currentSnapshot.thesis && thesesDiv}
          {currentSnapshot.assumptions.length > 0 && assumptionsDiv}
          {currentSnapshot.argument.length > 0 && argumentDiv()}
          {currentSnapshot.counter_argument.length > 0 && counterArgumentDiv()}
          {currentSnapshot.explanation && explanationDiv()}
          {currentSnapshot.lastPrompt && lastPromptDiv}
          {prompt && promptDiv}
        </div>
      </div>
      {loadingIndicator}
    </div>
  )

  const placeholderText =
    currentSnapshot.argMode == 'thesis' ? 'Enter thesis' :
    userMode == 'input' ? 'Enter proposition' : ''

  const handleEnter = (prompt: string) => {
    if (currentSnapshot.argMode == 'thesis') {
      handleThesis(prompt)
    }
    else if (userMode == 'input') {
      handleUserJustify(prompt)
    }
    setInputText('')
  }

  const userDiv = (
    <div className="p-4 flex gap-2 w-[100%] flex-wrap">
      <input
        ref={inputRef}
        className="flex-1 px-4 bg-slate-200 rounded-full focus:outline-2 focus:outline-indigo-500 dark:bg-zinc-800 "
        value={inputText}
        disabled={!(currentSnapshot.argMode == 'thesis' || userMode == 'input')}
        onChange={e => setInputText(e.target.value)}
        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
          if (e.key == 'Enter') {
            handleEnter(inputText)
            e.preventDefault()
          }
        }}
        placeholder={placeholderText}
        tabIndex={1}
      />
      <button
        className={bigButtonClassNames}
        disabled={!(currentSnapshot.argMode == 'thesis' || userMode == 'input')}
        onClick={() => handleEnter(inputText)}
        tabIndex={2}>
        Enter
      </button>
    </div>
  )

  return (
    <>
      {conversation.snapshots.length < 2 ? undefined :
        <div className="fixed top-4 right-4 z-10 flex gap-2">
          <button
            disabled={snapshotIndex <= 0 || userMode == 'waiting'}
            onClick={handleUndo}
            className={bigButtonClassNames + ' disabled:bg-slate-200 dark:disabled:bg-zinc-800'}>
              Undo
          </button>
          <button
            disabled={snapshotIndex >= conversation.snapshots.length - 1
              || userMode == 'waiting'}
            onClick={handleRedo}
            className={bigButtonClassNames + ' disabled:bg-slate-200 dark:disabled:bg-zinc-800'}>
              Redo
          </button>
          <button
            onClick={handleCopy}
            className={bigButtonClassNames}>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      }
      {messagesDiv}
      {userDiv}
    </>
  )
}

export default Conversation
