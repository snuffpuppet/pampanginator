/**
 * Zustand vocabulary store — Decision 8.
 *
 * State and actions for the vocabulary search and contribution features.
 * Components read from here; api.ts is the only place fetch() is called.
 */

import { create } from 'zustand'
import { searchVocabulary, addVocabularyEntry } from '../services/api'
import type { VocabSearchResult, AddVocabRequest } from '../services/api'

interface VocabularyStore {
  vocabularyResults: VocabSearchResult[]
  isSearching: boolean
  lastQuery: string
  searchError: string | null

  isAdding: boolean
  addedEntry: VocabSearchResult | null
  addError: string | null

  searchVocabulary: (query: string) => Promise<void>
  addVocabularyEntry: (entry: AddVocabRequest) => Promise<VocabSearchResult>
  clearResults: () => void
  clearAddedEntry: () => void
}

export const useVocabulary = create<VocabularyStore>((set) => ({
  vocabularyResults: [],
  isSearching: false,
  lastQuery: '',
  searchError: null,

  isAdding: false,
  addedEntry: null,
  addError: null,

  searchVocabulary: async (query) => {
    if (!query.trim()) {
      set({ vocabularyResults: [], lastQuery: '', searchError: null })
      return
    }
    set({ isSearching: true, lastQuery: query, searchError: null })
    try {
      const data = await searchVocabulary(query)
      set({ vocabularyResults: data.results, isSearching: false })
    } catch (err) {
      set({
        isSearching: false,
        searchError: err instanceof Error ? err.message : 'Search failed',
      })
    }
  },

  addVocabularyEntry: async (entry) => {
    set({ isAdding: true, addError: null, addedEntry: null })
    try {
      const result = await addVocabularyEntry(entry)
      set({ isAdding: false, addedEntry: result })
      return result
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to add entry'
      set({ isAdding: false, addError: msg })
      throw err
    }
  },

  clearResults: () => set({ vocabularyResults: [], lastQuery: '', searchError: null }),
  clearAddedEntry: () => set({ addedEntry: null, addError: null }),
}))
