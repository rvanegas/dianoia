export function thesisMarkdown(response) {
  const responseObject = JSON.parse(response)
  let md = '**Thesis:**\n\n'
  md += responseObject.thesis + '\n\n'
  md += '**Counter-Thesis:**\n\n'
  md += responseObject.counter_thesis + '\n\n'
  return md
}

export function developmentMarkdown(response) {
  const responseObject = JSON.parse(response)
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
      md += `_[${justifier}]_\n\n`
    })
  }

  argumentMarkdown(responseObject.argument)
  if (responseObject.counter_argument.length != 0) {
    md += '**Counter-Argument:**\n\n'
    argumentMarkdown(responseObject.counter_argument)
  }
  return md
}

export function exportMarkdown(messages) {
  let md = ''
  messages.map((message, i) => {
    if (i == 1) {
      md += '## Dianoia:\n\n'
      md += thesisMarkdown(message.content)
      md += '\n\n'
    } else if (message.role == 'assistant') {
      md += '## Dianoia:\n\n'
      md += developmentMarkdown(message.content)
      md += '\n\n'
    } else {
      md += '## You:\n\n'
      md += message.content
      md += '\n\n'
    }
  })
  return md
}
