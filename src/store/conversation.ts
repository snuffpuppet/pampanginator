/**
 * Zustand conversation store — Decision 8.
 *
 * Single source of truth for what the app knows about the current
 * conversation. Every state change is a named, readable action.
 *
 * Reading this file tells you everything the app can do — without
 * reading a single component.
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { streamChat } from '../services/api'
import type { Mode } from '../services/api'

export type { Mode }

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
}

const WELCOME: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    "*Mayap a abak!* I am **Ading** — your Kapampangan language companion.\n\n" +
    "I'm here to help you learn, practise, translate, and understand this beautiful language. " +
    "What would you like to work on today?",
  timestamp: Date.now(),
}

interface ConversationStore {
  messages: Message[]
  isStreaming: boolean
  streamingText: string
  sourcesUsed: boolean
  activeScenario: string | null

  /** Send a user message and stream Ading's response into the store. */
  sendMessage: (text: string, mode?: Mode, scenarioName?: string) => Promise<void>

  setActiveScenario: (scenario: string | null) => void
  clearConversation: () => void
}

export const useConversation = create<ConversationStore>()(
  persist(
    (set, get) => ({
      messages: [WELCOME],
      isStreaming: false,
      streamingText: '',
      sourcesUsed: false,
      activeScenario: null,

      sendMessage: async (text, mode = 'chat', scenarioName) => {
        if (get().isStreaming) return

        // Snapshot history before the new user message for the API call
        const history = get().messages

        set((s) => ({
          messages: [
            ...s.messages,
            { id: crypto.randomUUID(), role: 'user', content: text, timestamp: Date.now() },
          ],
          isStreaming: true,
          streamingText: '',
          sourcesUsed: false,
        }))

        const apiMessages = [
          ...history.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content })),
          { role: 'user' as const, content: text },
        ]

        try {
          const result = await streamChat(
            apiMessages,
            (chunk) => set((s) => ({ streamingText: s.streamingText + chunk })),
            mode,
            scenarioName,
          )
          set((s) => ({
            messages: [
              ...s.messages,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: s.streamingText,
                timestamp: Date.now(),
              },
            ],
            streamingText: '',
            isStreaming: false,
            sourcesUsed: result.sourcesUsed,
          }))
        } catch {
          set((s) => ({
            messages: [
              ...s.messages,
              {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: '*Pasensya na* — something went wrong. Please try again.',
                timestamp: Date.now(),
              },
            ],
            streamingText: '',
            isStreaming: false,
          }))
        }
      },

      setActiveScenario: (scenario) => set({ activeScenario: scenario }),

      clearConversation: () =>
        set({
          messages: [{ ...WELCOME, timestamp: Date.now() }],
          streamingText: '',
          isStreaming: false,
          sourcesUsed: false,
        }),
    }),
    {
      name: 'kapilator-chat',
      partialize: (state) => ({ messages: state.messages }),
    },
  ),
)
