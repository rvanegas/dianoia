import { ChevronRight } from 'lucide-react'
import { useState } from 'react'

type UserMode = 'waiting' | 'ready' | 'input'

interface ThesisActionsProps {
  thesisType: 'thesis' | 'counter_thesis'
  userMode: UserMode
  onArgue: (thesisType: string) => Promise<void>
}

export default function ThesisActions({
  thesisType,
  userMode,
  onArgue
}: ThesisActionsProps) {
  const [isOpen, setIsOpen] = useState(false)
  const isDisabled = userMode === 'waiting'

  const actionItems = [
    {
      label: 'Argue',
      onClick: async () => {
        await onArgue(thesisType)
        setIsOpen(false)
      },
      show: true
    }
  ].filter(item => item.show)

  if (actionItems.length === 0) {
    return null
  }

  return (
    <div 
      className="relative -ml-8"
      onMouseEnter={() => !isDisabled && setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        disabled={isDisabled}
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center justify-center pl-3 py-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md disabled:opacity-25 disabled:cursor-not-allowed"
      >
        <ChevronRight className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute left-6 top-0 bg-gray-100 dark:bg-gray-700 shadow-lg z-10">
          <div className="flex py-0.5">
            {actionItems.map((item, index) => (
              <button
                key={index}
                onClick={item.onClick}
                className="px-2 py-0.5 text-xs text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 whitespace-nowrap"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
} 