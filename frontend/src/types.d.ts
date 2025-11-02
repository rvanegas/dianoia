
type ArgMode = 'thesis' | 'development'

export type StepType = {
  symbol: string
  proposition: string
  justifiers: string[]
  truth: string
  valid: string
}

type ConversationSnapshot = {
  thesis: string
  counter_thesis: string
  presupposition: string
  argument: StepType[]
  counter_argument: StepType[]
  assumptions: StepType[]
  lastPrompt: string
  argMode: ArgMode
  evaluationsPending: boolean
  explanation: string | undefined
  formalization: string[] | undefined
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
