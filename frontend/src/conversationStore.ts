import { create } from 'zustand'
import { produce } from 'immer'
import type { ConversationType } from './types'

interface ConversationState {
  conversations: ConversationType[]
  currentConversationIndex: number
  nextConversationId: number
  
  updateCurrentConversation: (conversation: ConversationType) => void
  setCurrentConversationIndex: (index: number) => void
  setNextConversationId: (id: number) => void
}

export const useConversationStore = create<ConversationState>((set) => ({
  conversations: [{ id: 1, name: '', initPrompt: undefined, snapshots: [] }],
  currentConversationIndex: 0,
  nextConversationId: 2,

  updateCurrentConversation: (conversation) => {
    set(produce((state) => {
      state.conversations[state.currentConversationIndex] = conversation
    }))
  },

  setCurrentConversationIndex: (index) => 
    set({ currentConversationIndex: index }),

  setNextConversationId: (id) => 
    set({ nextConversationId: id })
}))
