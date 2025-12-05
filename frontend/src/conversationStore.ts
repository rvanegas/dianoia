import { create } from 'zustand'
import { produce } from 'immer'
import type { ConversationType } from './types'

interface ConversationState {
  conversations: ConversationType[]
  currentConversationIndex: number
  nextConversationId: number
  
  updateCurrentConversation: (conversation: ConversationType) => void
  addConversation: (conversation: ConversationType) => void
  saveConversationName: (conversationId: number, name: string) => void
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

  addConversation: (conversation) => {
    set(produce((state) => {
      state.conversations.push(conversation)
      state.currentConversationIndex = state.conversations.length - 1
      state.nextConversationId = conversation.id + 1
    }))
  },

  saveConversationName: (conversationId, name) => {
    set(produce((state) => {
      const conversation = state.conversations.find((c: ConversationType) => c.id === conversationId)
      if (conversation) {
        conversation.name = name
      }
    }))
  },

  setCurrentConversationIndex: (index) => 
    set({ currentConversationIndex: index }),

  setNextConversationId: (id) => 
    set({ nextConversationId: id })
}))
