import { ChevronRight } from 'lucide-react'
import { useState } from 'react'

type ActionType = 'remove' | 'assume' | 'explain'
type UserMode = 'waiting' | 'ready' | 'input'

interface PropositionActionsProps {
  step: any
  stepIndex: number
  loc: string
  argumentLength: number
  userMode: UserMode
  onAIJustify: (loc: string, stepIndex: number) => Promise<void>
  onUserJustify: (loc: string, stepIndex: number) => void
  onAssume: (action: ActionType, prompt: string, loc: string, stepIndex: number) => Promise<void>
  onRemove: (action: ActionType, prompt: string, loc: string, stepIndex: number) => Promise<void>
  onDispute: (step: any) => Promise<void>
  onExplain: (action: ActionType, prompt: string, loc: string, stepIndex: number) => Promise<void>
  setUserMode: (mode: UserMode) => void
  setTargetLoc: (loc: string) => void
  setTargetIndex: (index: number) => void
}

export default function PropositionActions({
  step,
  stepIndex,
  loc,
  argumentLength,
  userMode,
  onAIJustify,
  onAssume,
  onRemove,
  onDispute,
  onExplain,
  setUserMode,
  setTargetLoc,
  setTargetIndex
}: PropositionActionsProps) {
  const [isOpen, setIsOpen] = useState(false)
  const isDisabled = userMode === 'waiting'
  const isLastStep = stepIndex === argumentLength - 1
  const hasJustifiers = step.justifiers.length > 0

  const actionItems = [
    {
      label: 'AI Justify',
      onClick: async () => {
        await onAIJustify(loc, stepIndex)
        setIsOpen(false)
      },
      show: true
    },
    {
      label: 'User Justify',
      onClick: () => {
        setUserMode('input')
        setTargetLoc(loc)
        setTargetIndex(stepIndex)
        setIsOpen(false)
      },
      show: true
    },
    {
      label: 'Assume',
      onClick: async () => {
        const prompt = `Assume proposition (${step.symbol})`
        await onAssume('assume', prompt, loc, stepIndex)
        setIsOpen(false)
      },
      show: !isLastStep && !hasJustifiers
    },
    {
      label: 'Remove',
      onClick: async () => {
        const prompt = `Remove proposition (${step.symbol})`
        await onRemove('remove', prompt, loc, stepIndex)
        setIsOpen(false)
      },
      show: !isLastStep
    },
    {
      label: 'Dispute',
      onClick: async () => {
        await onDispute(step)
        setIsOpen(false)
      },
      show: !isLastStep
    },
    {
      label: 'Explain',
      onClick: async () => {
        const prompt = `Explain inference to propositon (${step.symbol})`
        await onExplain('explain', prompt, loc, stepIndex)
        setIsOpen(false)
      },
      show: hasJustifiers
    }
  ].filter(item => item.show)

  if (actionItems.length === 0) {
    return null
  }

  return (
    <div 
      className="relative -ml-8"
      onMouseEnter={() => !isDisabled && setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        disabled={isDisabled}
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center justify-center pl-3 py-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md disabled:opacity-25 disabled:cursor-not-allowed"
      >
        <ChevronRight className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute left-12 top-0 bg-gray-100 dark:bg-gray-700 shadow-lg z-10">
          <div className="flex py-0.5">
            {actionItems.map((item, index) => (
              <button
                key={index}
                onClick={item.onClick}
                className="px-2 py-0.5 text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 whitespace-nowrap"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 