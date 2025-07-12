import type { ThesesType, StepType, ArgsType } from './types'

export function thesisMarkdown(theses: ThesesType) {
  let md = '**Thesis:**\n\n'
  md += theses.thesis + '\n\n'
  md += '**Counter-Thesis:**\n\n'
  md += theses.counter_thesis + '\n\n'
  md += '**Presupposition:**\n\n'
  md += theses.presupposition + '\n\n'
  return md
}

export function developmentMarkdown(args: ArgsType) {
  let md = ''

  const assumptionsMarkdown = (assumptions: StepType[]) => {
    assumptions.forEach(item => {
      md += `(${item.symbol}) `
      md += `${item.proposition}`
      md += '\n\n'
    })
  }

  const argumentMarkdown = (steps: StepType[]) => {
    steps.forEach(step => {
      md += `(${step.symbol}) `
      md += `${step.proposition} `

      let justifier = ''
      let value = `${step.truth}`
      if (step.justifiers.length == 0) {
        justifier = 'premise'
      }
      else {
        justifier = 'from ' + step.justifiers.join(', ')
        value += `, ${step.valid}`
      }
      md += `_[${justifier}; ${value}]_\n\n`
    })
  }

  if (args.assumptions.length != 0) {
    md += '**Assumptions:**\n\n'
    assumptionsMarkdown(args.assumptions)
  }
  md += '**Argument:**\n\n'
  argumentMarkdown(args.argument)
  md += '**Counter-Argument:**\n\n'
  argumentMarkdown(args.counter_argument)
  return md
}

export function exportMarkdown(theses: ThesesType, args: ArgsType) {
  let md = ''
  md += thesisMarkdown(theses)
  md += developmentMarkdown(args)
  return md
}
