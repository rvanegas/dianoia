
type ArgMode = 'thesis' | 'development'

export type StepType = {
  symbol: string
  proposition: string
  justifiers: string[]
  truth: string
  valid: string
}

type ConversationSnapshot = {
  argument: StepType[]
  assumptions: StepType[]
  argMode: ArgMode
  evaluationsPending: boolean
  explanation: string | undefined
  file_ids: string[]
}

type ConversationType = {
  id: number
  name: string
  initPrompt: string | undefined
  snapshots: ConversationSnapshot[]
}

export type FileType = {
  file_id: string
  filename: string
}
