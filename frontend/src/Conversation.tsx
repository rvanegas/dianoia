import './App.css'

import {useEffect, useRef} from 'react'

import type {StepType, ConversationType, FileType} from './types'
import {exportMarkdown} from './markdown'
import {useConversationState, useConversationActions, useConversationNavigation} from './ConversationHooks'

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`
const smallButtonClassNames = `inline text-xs px-1 py-0.5 ml-1
  hover:text-white hover:bg-gray-500 disabled:opacity-[25%]`
const headingClassNames = `text-lg font-bold`

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
  const {
    snapshotRenderCount,
    snapshotIndex,
    setSnapshotIndex,
    currentSnapshot,
    userMode,
    setUserMode,
    targetLoc,
    setTargetLoc,
    targetIndex,
    setTargetIndex,
    inputText,
    setInputText,
    prompt,
    setPrompt,
    copied,
    setCopied,
    inputRef,
    saveSnapshot,
    argLoc
  } = useConversationState(conversation, setConversation)

  const {
    handleThesis,
    handleAIJustify,
    handleArgue,
    handleUserJustify,
    evaluateSteps,
    handleAction,
    handleDispute
  } = useConversationActions(
    currentSnapshot,
    userMode,
    setUserMode,
    setPrompt,
    setInputText,
    targetLoc,
    targetIndex,
    argLoc,
    saveSnapshot,
    createConversationFromProposition
  )

  const {
    handleUndo,
    handleRedo
  } = useConversationNavigation(
    snapshotIndex,
    conversation,
    setSnapshotIndex,
    setUserMode,
    snapshotRenderCount
  )

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
      evaluateSteps(snapshotRenderCount)
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
          ({step.symbol}) {step.proposition} {argument.length == 1 ? undefined : scoreSpan()}
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
