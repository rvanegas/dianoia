import ActionMenu from './ActionMenu'

type ActionType = 'remove' | 'assume' | 'explain'
type UserMode = 'waiting' | 'ready' | 'input'

interface PropositionActionsProps {
  step: any
  stepIndex: number
  loc: string
  argumentLength: number
  userMode: UserMode
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
    // DISABLED: AI Justify action - replaced by new agent system
    // {
    //   label: 'AI Justify',
    //   onClick: async () => {
    //     await onAIJustify(loc, stepIndex)
    //   },
    //   show: loc !== 'assumptions'
    // },
    {
      label: 'User Justify',
      onClick: () => {
        setUserMode('input')
        setTargetLoc(loc)
        setTargetIndex(stepIndex)
      },
      show: loc !== 'assumptions'
    },
    {
      label: 'Assume',
      onClick: async () => {
        await onAssume('assume', loc, stepIndex, `Assume proposition (${step.symbol})`)
      },
      show: loc !== 'assumptions' && !isLastStep && !hasJustifiers
    },
    {
      label: 'Remove',
      onClick: async () => {
        await onRemove('remove', loc, stepIndex, `Remove proposition (${step.symbol})`)
      },
      show: loc === 'assumptions' || !isLastStep
    },
    {
      label: 'Dispute',
      onClick: async () => {
        await onDispute(step)
      },
      show: loc === 'assumptions' || !isLastStep
    },
    {
      label: 'Explain',
      onClick: async () => {
        await onExplain('explain', loc, stepIndex, `Explain inference to proposition (${step.symbol})`)
      },
      show: loc !== 'assumptions' && hasJustifiers
    }
  ]

  return (
    <ActionMenu
      actionItems={actionItems}
      userMode={userMode}
    />
  )
}
