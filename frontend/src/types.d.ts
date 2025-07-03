export type ThesesType = {
  thesis: string
  counter_thesis: string
  presupposition: string
}

export type StepType = {
  index: string
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

type UserMode = 'thesis' | 'development'

// thesis -> waiting -> thesis
// thesis -> waiting -> development
// development -> waiting -> development
// development -> inputProposition -> waiting -> development

type ConversationSnapshot = {
  theses: ThesesType
  args: ArgsType
  argErrors: ArgErrors
  lastPrompt: string
  userMode: UserMode
}

type ConversationType = {
  id: number
  name: string
  initPrompt: string
  snapshots: ConversationSnapshot[]
}
