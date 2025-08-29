import { create } from 'zustand'
import { produce } from 'immer'
import type { ConversationType, ConversationSnapshot } from './types'

export function initialSnapshot(): ConversationSnapshot {
  return {
    assumptions: [],
    argument: [],
    explanation: '',
    argMode: 'thesis',
    file_ids: []
  }
}

interface ConversationState {
  conversations: ConversationType[]
  currentConversationIndex: number
  currentSnapshotIndex: number
  nextConversationId: number
  userMode: 'waiting' | 'ready' | 'input'
  snapshotRenderCount: number
  sessionId: string
  
  updateCurrentConversation: (conversation: ConversationType) => void
  addConversation: (conversation: ConversationType) => void
  saveConversationName: (conversationId: number, name: string) => void
  saveSnapshot: (conversationId: number, snapshotIndex: number, snapshot: ConversationSnapshot) => void
  saveSnapshotInPlace: (conversationId: number, snapshotIndex: number, snapshot: ConversationSnapshot) => void
  saveAgentResults: (conversationId: number, snapshotIndex: number, agentResults: any) => void
  setCurrentConversationIndex: (index: number) => void
  setCurrentSnapshotIndex: (index: number) => void
  setUserMode: (mode: 'waiting' | 'ready' | 'input') => void
  setSnapshotRenderCount: (count: number) => void
  setNextConversationId: (id: number) => void
  getCurrentConversationState: () => { conversation: ConversationType, snapshotIndex: number }
  getCurrentConversationId: () => number
  createConversationFromProposition: (proposition: string) => void
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  conversations: [{ id: 1, name: '', initPrompt: undefined, snapshots: [initialSnapshot()] }],
  currentConversationIndex: 0,
  currentSnapshotIndex: 0,
  nextConversationId: 2,
  userMode: 'ready',
  snapshotRenderCount: 0,
  sessionId: crypto.randomUUID(),

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

  saveSnapshot: (conversationId, snapshotIndex, snapshot) => {
    // console.log('🔄 Store saveSnapshot called:', { conversationId, snapshotIndex, snapshot })
    set(produce((state) => {
      const conversation = state.conversations.find((c: ConversationType) => c.id === conversationId)
      if (conversation) {
        // Remove snapshots after the current index and add the new one
        conversation.snapshots.splice(snapshotIndex + 1)
        conversation.snapshots.push(snapshot)
        // Update the current snapshot index to point to the new snapshot
        state.currentSnapshotIndex = conversation.snapshots.length - 1
        // Increment render count
        state.snapshotRenderCount += 1
        // console.log('✅ Store saveSnapshot completed. New snapshots length:', conversation.snapshots.length)
      } else {
        // console.log('❌ Store saveSnapshot: conversation not found for id:', conversationId)
      }
    }))
  },

  saveSnapshotInPlace: (conversationId, snapshotIndex, snapshot) => {
    set(produce((state) => {
      const conversation = state.conversations.find((c: ConversationType) => c.id === conversationId)
      if (conversation) {
        // Replace the snapshot at the specified index
        conversation.snapshots[snapshotIndex] = snapshot
      }
    }))
  },

  saveAgentResults: (conversationId, snapshotIndex, agentResults) => {
    set(produce((state) => {
      const conversation = state.conversations.find((c: ConversationType) => c.id === conversationId)
      if (conversation && conversation.snapshots[snapshotIndex]) {
        // Update the agent results for the specific snapshot
        conversation.snapshots[snapshotIndex].agentResults = agentResults
      }
    }))
  },

  setCurrentConversationIndex: (index) => 
    set(produce((state) => {
      state.currentConversationIndex = index
      // Set currentSnapshotIndex to the last snapshot of the selected conversation
      const conversation = state.conversations[index]
      if (conversation && conversation.snapshots.length > 0) {
        state.currentSnapshotIndex = conversation.snapshots.length - 1
      } else {
        state.currentSnapshotIndex = 0
      }
    })),

  setCurrentSnapshotIndex: (index) => 
    set({ currentSnapshotIndex: index }),

  setUserMode: (mode) => 
    set({ userMode: mode }),

  setSnapshotRenderCount: (count) => 
    set({ snapshotRenderCount: count }),

  setNextConversationId: (id) => 
    set({ nextConversationId: id }),

  getCurrentConversationState: () => {
    const state = get()
    return {
      conversation: state.conversations[state.currentConversationIndex],
      snapshotIndex: state.currentSnapshotIndex
    }
  },

  getCurrentConversationId: () => {
    const state = get()
    return state.conversations[state.currentConversationIndex].id
  },

  createConversationFromProposition: (proposition: string) => {
    const state = get()
    const newConversation = {
      id: state.nextConversationId,
      name: '',
      initPrompt: proposition,
      snapshots: [initialSnapshot()]
    }
    
    // Call the existing addConversation function
    set(produce((state) => {
      state.conversations.push(newConversation)
      state.currentConversationIndex = state.conversations.length - 1
      state.nextConversationId = newConversation.id + 1
    }))
    
    // Reset currentSnapshotIndex to 0 for new conversation
    set({ currentSnapshotIndex: 0 })
  }
}))
