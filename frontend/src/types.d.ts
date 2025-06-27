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
