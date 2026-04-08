import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

interface ChatStore {
  messages: Message[]
  isStreaming: boolean
  streamingText: string
  addUserMessage: (content: string) => void
  appendStreaming: (text: string) => void
  finalizeStream: () => void
  clearSession: () => void
  setStreaming: (val: boolean) => void
}

const WELCOME: Message = {
  id: 'welcome',
  role: 'assistant',
  content: '*Mayap a abak!* I am **Ading** — your Kapampangan language companion.\n\nI\'m here to help you learn, practise, translate, and understand this beautiful language. What would you like to work on today?',
  timestamp: Date.now(),
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      messages: [WELCOME],
      isStreaming: false,
      streamingText: '',

      addUserMessage: (content) =>
        set((state) => ({
          messages: [
            ...state.messages,
            { id: crypto.randomUUID(), role: 'user', content, timestamp: Date.now() },
          ],
        })),

      appendStreaming: (text) =>
        set((state) => ({ streamingText: state.streamingText + text })),

      finalizeStream: () =>
        set((state) => {
          if (!state.streamingText) return { isStreaming: false }
          return {
            messages: [
              ...state.messages,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: state.streamingText,
                timestamp: Date.now(),
              },
            ],
            streamingText: '',
            isStreaming: false,
          }
        }),

      clearSession: () =>
        set({ messages: [{ ...WELCOME, timestamp: Date.now() }], streamingText: '', isStreaming: false }),

      setStreaming: (val) => set({ isStreaming: val }),
    }),
    {
      name: 'kapilator-chat',
      partialize: (state) => ({ messages: state.messages }),
    }
  )
)
