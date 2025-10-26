
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
  explanation: string | undefined
  formalization: string[] | undefined
  vector_store_id: string | undefined // ongoing context
}

type ConversationType = {
  id: number
  name: string
  initPrompt: string | undefined
  vector_store_id: string | undefined // initial context
  snapshots: ConversationSnapshot[]
}

export type FileType = {
  vector_store_id: string
  filename: string
}
