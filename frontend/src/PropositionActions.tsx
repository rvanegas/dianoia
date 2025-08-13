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
  onAssume: (action: ActionType, loc: string, stepIndex: number, errorLabel: string) => Promise<void>
  onRemove: (action: ActionType, loc: string, stepIndex: number, errorLabel: string) => Promise<void>
  onDispute: (step: any) => Promise<void>
  onExplain: (action: ActionType, loc: string, stepIndex: number, errorLabel: string) => Promise<void>
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
        await onAssume('assume', loc, stepIndex, `Assume proposition (${step.symbol})`)
      },
      show: !isLastStep && !hasJustifiers
    },
    {
      label: 'Remove',
      onClick: async () => {
        await onRemove('remove', loc, stepIndex, `Remove proposition (${step.symbol})`)
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
        await onExplain('explain', loc, stepIndex, `Explain inference to proposition (${step.symbol})`)
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
