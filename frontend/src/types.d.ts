export type ThesesType = {
  thesis: string
  counter_thesis: string
  presupposition: string
}

export type StepType = {
  symbol: string
  proposition: string
  justifiers: string[]
  truth: number
  valid: number
}

export type ArgsType = {
  argument: StepType[]
  counter_argument: StepType[]
  assumptions: StepType[]
}

type ArgMode = 'thesis' | 'development'

type ConversationSnapshot = {
  theses: ThesesType
  args: ArgsType
  lastPrompt: string
  argMode: ArgMode
  explanation: string | undefined
  formalization: string[] | undefined
}

type ConversationType = {
  id: number
  name: string
  initPrompt: string | undefined
  vector_store_id: string | undefined
  snapshots: ConversationSnapshot[]
}

export type FileType = {
  vector_store_id: string
  filename: string
}
