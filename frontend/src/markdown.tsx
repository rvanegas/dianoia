import type {StepType, ConversationSnapshot} from './types'

export function thesisMarkdown(currentSnapshot: ConversationSnapshot) {
  let md = '**Thesis:**\n\n'
  md += currentSnapshot.thesis + '\n\n'
  return md
}

export function developmentMarkdown(currentSnapshot: ConversationSnapshot) {
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

  if (currentSnapshot.assumptions.length != 0) {
    md += '**Assumptions:**\n\n'
    assumptionsMarkdown(currentSnapshot.assumptions)
  }
  md += '**Argument:**\n\n'
  argumentMarkdown(currentSnapshot.argument)
  return md
}

export function exportMarkdown(currentSnapshot: ConversationSnapshot) {
  let md = ''
  md += thesisMarkdown(currentSnapshot)
  md += developmentMarkdown(currentSnapshot)
  return md
}
