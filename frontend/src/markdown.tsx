
export function responseMarkdown(response) {
  const responseObject = JSON.parse(response)
  let md = '**Argument:**\n\n'

  const argumentMarkdown = argument => {
    argument.forEach(item => {
      md += `${item.index}. `
      md += `${item.proposition} `
      md += `_[${item.justifier}]_\n\n`
    })
  }

  argumentMarkdown(responseObject.argument)
  if (responseObject.counter_argument.length != 0) {
    md += '**Counter-Argument:**\n\n'
    argumentMarkdown(responseObject.counter_argument)
  }
  md += `**Explanation:**\n\n${responseObject.explanation}\n`
  return md
}

export function exportMarkdown(messages) {
  let md = ''
  messages.map(message => {
    console.log('message', message)
    if (message.role == 'assistant') {
      md += '## Dianoia:\n\n'
      md += responseMarkdown(message.content)
      md += '\n\n'
    } else {
      md += '## You:\n\n'
      md += message.content
      md += '\n\n'
    }
  })
  return md
}
