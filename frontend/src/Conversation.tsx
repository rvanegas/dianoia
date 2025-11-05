import './App.css'

import {useEffect, useRef} from 'react'

import type {StepType, ConversationType, FileType} from './types'
import {exportMarkdown} from './markdown'
import {useConversationState, useConversationActions, useConversationNavigation} from './ConversationHooks'
import PropositionActions from './PropositionActions'
import ThesisActions from './ThesisActions'

const bigButtonClassNames = `bg-indigo-600 hover:bg-indigo-500
  text-white font-bold px-4 py-2 rounded-md`

// Reusable FlexTable component
const FlexTable = ({ children }: { children: React.ReactNode }) => (
  <div className="flex flex-col">
    {children}
  </div>
)

const FlexRow = ({ 
  label, 
  children, 
  chevron 
}: { 
  label?: string
  children?: React.ReactNode
  chevron?: React.ReactNode
}) => (
  <div className="flex">
    <div className="w-[40px] flex-shrink-0">{chevron}</div>
    <div className={label ? "text-lg font-bold text-left" : "text-left"}>{label || children}</div>
  </div>
)

// Section wrapper component
const Section = ({ children }: { children: React.ReactNode }) => (
  <div className="mb-2">
    {children}
  </div>
)

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
      const actions = (
        <PropositionActions
          step={step}
          stepIndex={step_index}
          loc={loc}
          argumentLength={argument.length}
          userMode={userMode}
          onAIJustify={handleAIJustify}
          onUserJustify={(loc, stepIndex) => {
            setUserMode('input')
            setTargetLoc(loc)
            setTargetIndex(stepIndex)
          }}
          onAssume={(action, prompt, loc, stepIndex) => handleAction(action, prompt, loc, stepIndex)}
          onRemove={(action, prompt, loc, stepIndex) => handleAction(action, prompt, loc, stepIndex)}
          onDispute={handleDispute}
          onExplain={(action, prompt, loc, stepIndex) => handleAction(action, prompt, loc, stepIndex)}
          setUserMode={setUserMode}
          setTargetLoc={setTargetLoc}
          setTargetIndex={setTargetIndex}
        />
      )

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

      const isEvaluated = argument.length > 1 || step.justifiers.length > 0
      return (
        <FlexRow 
          key={step_index}
          chevron={actions}
        >
          ({step.symbol}) {step.proposition} {isEvaluated && scoreSpan()}
        </FlexRow>
      )
    })
    return <div>{argumentSteps}</div>
  }

  const argumentDiv = () => (
    <div>{argumentNode('argument', currentSnapshot.argument)}</div>
  )

  const counterArgumentDiv = () => (
    <div>{argumentNode('counter_argument', currentSnapshot.counter_argument)}</div>
  )

  const assumptionsDiv = (
    <div>
      {currentSnapshot.assumptions.map((step, step_index) => {
        const actions = (
          <PropositionActions
            step={step}
            stepIndex={step_index}
            loc="assumptions"
            argumentLength={currentSnapshot.assumptions.length}
            userMode={userMode}
            onAIJustify={handleAIJustify}
            onUserJustify={(loc, stepIndex) => {
              setUserMode('input')
              setTargetLoc(loc)
              setTargetIndex(stepIndex)
            }}
            onAssume={(action, prompt, loc, stepIndex) => handleAction(action, prompt, loc, stepIndex)}
            onRemove={(action, prompt, loc, stepIndex) => handleAction(action, prompt, loc, stepIndex)}
            onDispute={handleDispute}
            onExplain={(action, prompt, loc, stepIndex) => handleAction(action, prompt, loc, stepIndex)}
            setUserMode={setUserMode}
            setTargetLoc={setTargetLoc}
            setTargetIndex={setTargetIndex}
          />
        )

        return (
          <FlexRow 
            key={step_index}
            chevron={actions}
          >
            ({step.symbol}) {step.proposition}
          </FlexRow>
        )
      })}
    </div>
  )

  // const thesesDiv = (
  //   <div>
  //     <div>
  //       {currentSnapshot.argument.length == 0 ? (
  //         <div className="flex items-start gap-2">
  //           <ThesisActions
  //             thesisType="thesis"
  //             userMode={userMode}
  //             onArgue={handleArgue}
  //           />
  //           <div className="flex-1">
  //             {currentSnapshot.thesis}
  //           </div>
  //         </div>
  //       ) : (
  //         <div>{currentSnapshot.thesis}</div>
  //       )}
  //     </div>
  //     <div>
  //       {currentSnapshot.counter_argument.length == 0 ? (
  //         <div className="flex items-start gap-2">
  //           <ThesisActions
  //             thesisType="counter_thesis"
  //             userMode={userMode}
  //             onArgue={handleArgue}
  //           />
  //           <div className="flex-1">
  //             {currentSnapshot.counter_thesis}
  //           </div>
  //         </div>
  //       ) : (
  //         <div>{currentSnapshot.counter_thesis}</div>
  //       )}
  //     </div>
  //     <div>{currentSnapshot.presupposition}</div>
  //   </div>
  // )



  // const lastPromptDiv = (
  //   <div>
  //     {currentSnapshot.lastPrompt}
  //   </div>
  // )

  // const promptDiv = (
  //   <div>
  //     {prompt}
  //   </div>
  // )

  const explanationDiv = () => {
    if (!currentSnapshot.formalization || currentSnapshot.formalization.length == 0) return
    return (
      <>
        <div>{currentSnapshot.formalization.map((prop, key) => (<div key={key}>{prop}</div>))}</div>
        <div>{currentSnapshot.explanation}</div>
      </>
    )
  }

  const snapshotId = snapshotIndex < 1 ? '' : `.${snapshotIndex}`

  const renderAssociatedFileNames = () => (
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
  );

  const messagesDiv = (
    <div className="flex flex-1 overflow-y-auto p-5 flex-col w-[100%] scroll-hide">
      <FlexTable>
        <Section>
          <FlexRow label="Id:" />
          <FlexRow>{conversation.id}{snapshotId}</FlexRow>
        </Section>
        {currentSnapshot.file_ids && currentSnapshot.file_ids.length > 0 && (
          <Section>
            <FlexRow label="Files:" />
            <FlexRow>{renderAssociatedFileNames()}</FlexRow>
          </Section>
        )}
        {currentSnapshot.thesis && (
          <Section>
            <FlexRow label="Thesis:" />
            <FlexRow
              chevron={
                currentSnapshot.argument.length == 0 ? (
                  <ThesisActions
                    thesisType="thesis"
                    userMode={userMode}
                    onArgue={handleArgue}
                  />
                ) : undefined
              }
            >
              {currentSnapshot.thesis}
            </FlexRow>
          </Section>
        )}
        {currentSnapshot.counter_thesis && (
          <Section>
            <FlexRow label="Counter-Thesis:" />
            <FlexRow
              chevron={
                currentSnapshot.counter_argument.length == 0 ? (
                  <ThesisActions
                    thesisType="counter_thesis"
                    userMode={userMode}
                    onArgue={handleArgue}
                  />
                ) : undefined
              }
            >
              {currentSnapshot.counter_thesis}
            </FlexRow>
          </Section>
        )}
        {currentSnapshot.assumptions.length > 0 && (
          <Section>
            <FlexRow label="Assumptions:" />
            {assumptionsDiv}
          </Section>
        )}
        {currentSnapshot.argument.length > 0 && (
          <Section>
            <FlexRow label="Argument:" />
            {argumentDiv()}
          </Section>
        )}
        {currentSnapshot.counter_argument.length > 0 && (
          <Section>
            <FlexRow label="Counter-Argument:" />
            {counterArgumentDiv()}
          </Section>
        )}
        {currentSnapshot.explanation && (
          <Section>
            <FlexRow label="Explanation:" />
            <FlexRow>{explanationDiv()}</FlexRow>
          </Section>
        )}
        {currentSnapshot.lastPrompt && (
          <Section>
            <FlexRow label="LastPrompt:" />
            <FlexRow>{currentSnapshot.lastPrompt}</FlexRow>
          </Section>
        )}
        {prompt && (
          <Section>
            <FlexRow label="Prompt:" />
            <FlexRow>{prompt}</FlexRow>
          </Section>
        )}
      </FlexTable>
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
