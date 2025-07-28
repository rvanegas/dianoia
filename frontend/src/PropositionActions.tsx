import ActionMenu from './ActionMenu'

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
  const isLastStep = stepIndex === argumentLength - 1
  const hasJustifiers = step.justifiers.length > 0

  const actionItems = [
    {
      label: 'AI Justify',
      onClick: async () => {
        await onAIJustify(loc, stepIndex)
      },
      show: true
    },
    {
      label: 'User Justify',
      onClick: () => {
        setUserMode('input')
        setTargetLoc(loc)
        setTargetIndex(stepIndex)
      },
      show: true
    },
    {
      label: 'Assume',
      onClick: async () => {
        const prompt = `Assume proposition (${step.symbol})`
        await onAssume('assume', prompt, loc, stepIndex)
      },
      show: !isLastStep && !hasJustifiers
    },
    {
      label: 'Remove',
      onClick: async () => {
        const prompt = `Remove proposition (${step.symbol})`
        await onRemove('remove', prompt, loc, stepIndex)
      },
      show: !isLastStep
    },
    {
      label: 'Dispute',
      onClick: async () => {
        await onDispute(step)
      },
      show: !isLastStep
    },
    {
      label: 'Explain',
      onClick: async () => {
        const prompt = `Explain inference to propositon (${step.symbol})`
        await onExplain('explain', prompt, loc, stepIndex)
      },
      show: hasJustifiers
    }
  ]

  return (
    <ActionMenu
      actionItems={actionItems}
      userMode={userMode}
    />
  )
} 