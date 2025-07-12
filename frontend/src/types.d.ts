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

type ArgErrors = {
  argument: string[]
  counter_argument: string[]
}

type ArgMode = 'thesis' | 'development'

type ConversationSnapshot = {
  theses: ThesesType
  args: ArgsType
  argErrors: ArgErrors
  lastPrompt: string
  argMode: ArgMode
}

type ConversationType = {
  id: number
  name: string
  initPrompt: string
  snapshots: ConversationSnapshot[]
}
