/**
 * All HTTP calls in one place — Decision 10.
 *
 * Nothing outside this file calls fetch(). Components and the store
 * import from here; if the backend URL or request format changes,
 * one file changes.
 */

import { buildVocabContext } from '../lib/lookup'

// ─── Types ────────────────────────────────────────────────────────────────────

export type Mode =
  | 'chat'
  | 'translation-en-kp'
  | 'translation-kp-en'
  | 'correction'
  | 'scenario'

export interface ApiMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface BackendStatus {
  backend: string
  modelA: string
  modelB: string
  hasOpenRouterKey: boolean
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

const LOOKUP_MODES: Mode[] = ['translation-en-kp', 'translation-kp-en', 'correction']

function buildUserContent(
  text: string,
  mode: Mode,
  vocabContext: string,
  scenarioName?: string,
): string {
  const ref = vocabContext ? `${vocabContext}\n\n` : ''
  switch (mode) {
    case 'translation-en-kp':
      return `${ref}[TRANSLATION: EN→KP] Translate to Kapampangan and provide a brief usage note: "${text}"`
    case 'translation-kp-en':
      return `${ref}[TRANSLATION: KP→EN] Translate this Kapampangan to English and note any grammar of interest: "${text}"`
    case 'correction':
      return `${ref}[ERROR CORRECTION MODE] Apply your five-step correction protocol to this Kapampangan sentence the learner wrote: "${text}"`
    case 'scenario':
      return `${ref}[SCENARIO: ${scenarioName ?? 'Conversation Practice'}] ${text}`
    default:
      return `${ref}${text}`
  }
}

async function readStream(
  body: ReadableStream<Uint8Array>,
  onChunk: (text: string) => void,
): Promise<{ interactionId: string | null }> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let interactionId: string | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') return { interactionId }
      try {
        const parsed = JSON.parse(data)
        if (parsed.text) onChunk(parsed.text)
        if (parsed.interaction_id) interactionId = parsed.interaction_id
      } catch { /* partial chunk — skip */ }
    }
  }
  return { interactionId }
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Stream a chat response from Ading.
 *
 * Enriches the last user message with authoritative vocabulary context and the
 * appropriate mode prefix, then opens an SSE connection and calls onChunk for
 * each text delta received.
 *
 * Returns { sourcesUsed: true } if kaikki.org reference data was injected.
 */
export async function streamChat(
  messages: ApiMessage[],
  onChunk: (text: string) => void,
  mode: Mode = 'chat',
  scenarioName?: string,
  endpoint = '/api/chat',
): Promise<{ sourcesUsed: boolean; interactionId: string | null }> {
  const userText = messages[messages.length - 1]?.content ?? ''
  const shouldLookup = LOOKUP_MODES.includes(mode) || userText.length < 200
  const vocabContext = shouldLookup ? await buildVocabContext(userText) : ''

  const processedMessages = messages.map((msg, i) =>
    i === messages.length - 1 && msg.role === 'user'
      ? { ...msg, content: buildUserContent(msg.content, mode, vocabContext, scenarioName) }
      : msg,
  )

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: processedMessages }),
  })

  if (!response.ok) throw new Error(`API error: ${response.status}`)
  if (!response.body) throw new Error('No response body')

  const { interactionId } = await readStream(response.body, onChunk)

  return { sourcesUsed: !!vocabContext, interactionId }
}

/**
 * Fetch the current backend configuration from the dev server.
 */
export async function getBackendStatus(): Promise<BackendStatus> {
  const res = await fetch('/api/status')
  if (!res.ok) throw new Error('Could not reach /api/status')
  return res.json() as Promise<BackendStatus>
}

// ─── Vocabulary ────────────────────────────────────────────────────────────────

export interface VocabSearchResult {
  id: string
  term: string
  meaning: string
  part_of_speech?: string
  aspect_forms?: Record<string, string>
  examples?: Array<{ kapampangan: string; english: string }>
  usage_notes?: string
  authority_level: number
  source?: string
  similarity_score: number
}

export interface VocabSearchResponse {
  query: string
  count: number
  results: VocabSearchResult[]
}

export interface AddVocabRequest {
  term: string
  meaning: string
  part_of_speech?: string
  aspect_forms?: Record<string, string>
  examples?: Array<{ kapampangan: string; english: string }>
  usage_notes?: string
  source?: string
  authority_level?: number
}

export async function searchVocabulary(query: string, limit = 6): Promise<VocabSearchResponse> {
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  const res = await fetch(`/api/vocabulary/search?${params}`)
  if (!res.ok) throw new Error(`Vocabulary search error: ${res.status}`)
  return res.json() as Promise<VocabSearchResponse>
}

export async function addVocabularyEntry(entry: AddVocabRequest): Promise<VocabSearchResult> {
  const res = await fetch('/api/vocabulary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
  if (!res.ok) throw new Error(`Add vocabulary error: ${res.status}`)
  return res.json() as Promise<VocabSearchResult>
}

// ─── Feedback ──────────────────────────────────────────────────────────────────

export interface FeedbackRequest {
  interaction_id?: string
  rating: 'thumbs_up' | 'thumbs_down'
  correction_kapampangan?: string
  correction_english?: string
  correction_note?: string
  corrected_by?: string
  authority_level?: number
}

export async function submitFeedback(body: FeedbackRequest): Promise<{ id: string }> {
  const res = await fetch('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Feedback error: ${res.status}`)
  return res.json() as Promise<{ id: string }>
}

// ─── Admin ─────────────────────────────────────────────────────────────────────

export interface FeedbackRecord {
  id: string
  interaction_id: string | null
  timestamp: string
  rating: 'thumbs_up' | 'thumbs_down'
  correction_kapampangan?: string
  correction_english?: string
  correction_note?: string
  corrected_by?: string
  authority_level: number
  reviewed: boolean
  applied: boolean
  interaction?: {
    user_message: string
    llm_response: string
    session_id: string
    model: string
  }
}

export async function getPendingFeedback(): Promise<FeedbackRecord[]> {
  const res = await fetch('/api/feedback/pending')
  if (!res.ok) throw new Error(`Feedback pending error: ${res.status}`)
  const data = await res.json()
  return data.records
}

export interface FeedbackFilters {
  rating?: string
  authority_level?: number
  applied?: boolean
  after?: string
  before?: string
}

export async function getAllFeedback(filters: FeedbackFilters = {}): Promise<FeedbackRecord[]> {
  const params = new URLSearchParams()
  if (filters.rating) params.set('rating', filters.rating)
  if (filters.authority_level != null) params.set('authority_level', String(filters.authority_level))
  if (filters.applied != null) params.set('applied', String(filters.applied))
  if (filters.after) params.set('after', filters.after)
  if (filters.before) params.set('before', filters.before)
  const res = await fetch(`/api/feedback?${params}`)
  if (!res.ok) throw new Error(`Feedback list error: ${res.status}`)
  const data = await res.json()
  return data.records
}

export async function approveFeedback(id: string, authorityLevel?: number): Promise<void> {
  const res = await fetch(`/api/feedback/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ authority_level: authorityLevel ?? null }),
  })
  if (!res.ok) throw new Error(`Approve error: ${res.status}`)
}

export async function rejectFeedback(id: string): Promise<void> {
  const res = await fetch(`/api/feedback/${id}/reject`, { method: 'POST' })
  if (!res.ok) throw new Error(`Reject error: ${res.status}`)
}

// ─── Knowledge sharing (admin) ─────────────────────────────────────────────────

export interface SyncStatus {
  mode: 'git' | 'sync' | 'shared_db'
  contributor_name: string
  last_seeded: string | null
  seeded_count: { vocabulary: number }
  local_additions: { vocabulary: number; grammar_nodes: number }
  canonical_url?: string
}

export interface PendingContribution {
  id: string
  submitted_at: string
  contributor: string
  contribution_type: 'vocabulary' | 'grammar_node' | 'grammar_edge'
  payload: Record<string, unknown>
  source_mode: string
  authority_level: number
  review_status: string
}

export interface UploadedContribution {
  manifest: Record<string, unknown>
  vocabulary: Record<string, unknown>[]
  grammar_nodes: Record<string, unknown>[]
  grammar_edges: Record<string, unknown>[]
  counts: { vocabulary: number; grammar_nodes: number; grammar_edges: number }
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const res = await fetch('/api/admin/sync/status')
  if (!res.ok) throw new Error(`Sync status error: ${res.status}`)
  return res.json() as Promise<SyncStatus>
}

export async function reseedFromCanonical(): Promise<{ vocabulary: number; grammar_nodes: number }> {
  const res = await fetch('/api/admin/sync/reseed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confirm: 'reseed' }),
  })
  if (!res.ok) throw new Error(`Reseed error: ${res.status}`)
  return res.json() as Promise<{ vocabulary: number; grammar_nodes: number }>
}

export async function downloadContributions(
  contributor: string,
  minAuthorityLevel: number,
  since?: string,
): Promise<void> {
  const res = await fetch('/api/admin/sync/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contributor, min_authority_level: minAuthorityLevel, since }),
  })
  if (!res.ok) throw new Error(`Export error: ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${contributor.toLowerCase().replace(/\s+/g, '_')}_contribution.zip`
  a.click()
  URL.revokeObjectURL(url)
}

export async function getPendingContributions(): Promise<PendingContribution[]> {
  const res = await fetch('/api/admin/contributions/pending')
  if (!res.ok) throw new Error(`Contributions pending error: ${res.status}`)
  const data = await res.json()
  return data.records
}

export async function uploadContributionZip(file: File): Promise<UploadedContribution> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/admin/contributions/upload', { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Upload error: ${res.status}`)
  return res.json() as Promise<UploadedContribution>
}

export async function approveContribution(id: string, reviewedBy?: string): Promise<void> {
  const res = await fetch(`/api/admin/contributions/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewed_by: reviewedBy ?? null }),
  })
  if (!res.ok) throw new Error(`Approve contribution error: ${res.status}`)
}

export async function rejectContribution(id: string, note?: string): Promise<void> {
  const res = await fetch(`/api/admin/contributions/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note: note ?? null }),
  })
  if (!res.ok) throw new Error(`Reject contribution error: ${res.status}`)
}

export async function downloadTrainingData(
  format: 'sft' | 'dpo',
  minAuthorityLevel: number,
  after?: string,
  before?: string,
): Promise<void> {
  const res = await fetch('/api/export/training-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ format, min_authority_level: minAuthorityLevel, after, before }),
  })
  if (!res.ok) throw new Error(`Export error: ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `training_${format}_level${minAuthorityLevel}.jsonl`
  a.click()
  URL.revokeObjectURL(url)
}
