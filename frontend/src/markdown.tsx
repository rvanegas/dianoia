export function thesisMarkdown(theses) {
  let md = '**Thesis:**\n\n'
  md += theses.thesis + '\n\n'
  md += '**Counter-Thesis:**\n\n'
  md += theses.counter_thesis + '\n\n'
  md += '**Presuppositions:**\n\n'
  md += theses.presuppositions + '\n\n'
  return md
}

export function developmentMarkdown(args) {
  let md = '**Argument:**\n\n'
  let justifier = ''

  const argumentMarkdown = argument => {
    argument.forEach(item => {
      md += `(${item.index}${item.changed ? '*' : ''}) `
      md += `${item.proposition} `
      if (item.justifiers.length == 0) {
        justifier = 'premise'
      } else {
        justifier = `from ${item.justifiers.join(', ')}`
      }
      md += `_[${justifier}; ${item.truth}]_\n\n`
    })
  }

  argumentMarkdown(args.argument)
  if (args.counter_argument.length != 0) {
    md += '**Counter-Argument:**\n\n'
    argumentMarkdown(args.counter_argument)
  }
  return md
}

export function exportMarkdown(theses, args) {
  let md = ''
  md += thesisMarkdown(theses)
  md += '\n\n'
  md += developmentMarkdown(args)
  md += '\n\n'
  return md
}
